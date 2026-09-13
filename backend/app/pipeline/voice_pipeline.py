import os

from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.observers.loggers.transcription_log_observer import TranscriptionLogObserver
from pipecat.observers.loggers.metrics_log_observer import MetricsLogObserver
from pipecat.observers.user_bot_latency_observer import UserBotLatencyObserver
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker, ProcessorUnusablePolicy
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.turns.user_start import MinWordsUserTurnStartStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies
from pipecat.workers.runner import WorkerRunner

from app.config.settings import get_settings
from app.pipeline.providers import create_llm, create_stt, create_tts


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments) -> None:
    settings = get_settings()
    stt, llm, tts = create_stt(settings), create_llm(settings), create_tts(settings)

    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            # Pipecat owns speech-end / interruption handling. This only avoids a
            # single accidental word cancelling the assistant.
            user_turn_strategies=UserTurnStrategies(
                start=[MinWordsUserTurnStartStrategy(min_words=settings.min_start_words)]
            ),
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )
    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            audio_out_sample_rate=24000,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
        observers=[
            # Pipecat emits per-service TTFB / processing and provider usage.
            MetricsLogObserver(),
            TranscriptionLogObserver(),
            _latency_observer(),
        ],
        processor_unusable_policy=ProcessorUnusablePolicy.END,
    )
    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)
    await runner.add_workers(worker)

    @transport.event_handler("on_client_connected")
    async def on_client_connected(_transport, _client):
        logger.info("Voice client connected; providers: stt={}, llm={}, tts={}", settings.stt_provider, settings.llm_provider, settings.tts_provider)

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(_transport, _client):
        logger.info("Voice client disconnected")
        await runner.cancel()

    await runner.run()


def _latency_observer() -> UserBotLatencyObserver:
    """Log actual speech-to-speech latency and its STT/LLM/TTS breakdown."""
    observer = UserBotLatencyObserver()

    @observer.event_handler("on_latency_measured")
    async def on_latency_measured(_observer, latency_seconds):
        logger.info("[VOICE] user-stop → first bot audio: {:.0f}ms", latency_seconds * 1000)

    @observer.event_handler("on_latency_breakdown")
    async def on_latency_breakdown(_observer, breakdown):
        for event in breakdown.chronological_events():
            logger.info("[VOICE] {}", event)

    return observer


async def bot(runner_args: RunnerArguments) -> None:
    if os.environ.get("TRANSPORT", "webrtc") != "webrtc":
        raise ValueError("This POC intentionally supports only TRANSPORT=webrtc")
    transport = await create_transport(
        runner_args,
        {"webrtc": lambda: TransportParams(audio_in_enabled=True, audio_out_enabled=True)},
    )
    await run_bot(transport, runner_args)
