"""Small provider factories. Add a provider here without changing transport or UI code."""

from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.tts import OpenAITTSService

from app.config.settings import Settings


def create_stt(settings: Settings):
    if settings.stt_provider == "deepgram":
        return DeepgramSTTService(
            api_key=settings.required_secret(settings.deepgram_api_key, "DEEPGRAM_API_KEY")
        )
    raise ValueError(f"Unsupported STT_PROVIDER: {settings.stt_provider}")


def create_llm(settings: Settings):
    if settings.llm_provider == "openai":
        return OpenAILLMService(
            api_key=settings.required_secret(settings.openai_api_key, "OPENAI_API_KEY"),
            settings=OpenAILLMService.Settings(
                model=settings.openai_model,
                system_instruction=settings.system_prompt,
            ),
        )
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


def create_tts(settings: Settings):
    if settings.tts_provider == "openai":
        return OpenAITTSService(
            api_key=settings.required_secret(settings.openai_api_key, "OPENAI_API_KEY"),
            settings=OpenAITTSService.Settings(
                model=settings.openai_tts_model,
                voice=settings.openai_tts_voice,
                instructions=settings.openai_tts_instructions,
            ),
        )
    if settings.tts_provider == "deepgram":
        return DeepgramTTSService(
            api_key=settings.required_secret(settings.deepgram_api_key, "DEEPGRAM_API_KEY"),
            settings=DeepgramTTSService.Settings(voice=settings.deepgram_tts_voice),
        )
    raise ValueError(f"Unsupported TTS_PROVIDER: {settings.tts_provider}")
