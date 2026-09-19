"""Small provider factories. Add a provider here without changing transport or UI code."""

from datetime import datetime
from zoneinfo import ZoneInfo

from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.services.openai.responses.llm import OpenAIResponsesLLMService
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
        now = datetime.now(ZoneInfo(settings.user_timezone))
        return OpenAIResponsesLLMService(
            api_key=settings.required_secret(settings.openai_api_key, "OPENAI_API_KEY"),
            settings=OpenAIResponsesLLMService.Settings(
                model=settings.openai_model,
                system_instruction=(
                    f"{settings.system_prompt} "
                    "Calendar and Todo data are accessed through the available tools. "
                    "Use get_schedule for calendar questions and the task tools for Todo questions. "
                    f"The user's timezone is {settings.user_timezone}. The current date and time "
                    f"at session start is {now.isoformat()}. For any question about now, today, "
                    "tomorrow, relative dates, or the current time, call get_current_datetime "
                    "instead of guessing. Use the tool's returned timezone and ISO timestamp. "
                    "For calendar times spoken by the user, treat the clock time as a wall-clock "
                    f"time in {settings.user_timezone}; pass local ISO timestamps and do not add Z "
                    "or convert the time to UTC unless the user explicitly names another timezone. "
                    "Do not claim that a separate Notion calendar connection is unavailable. "
                    "If a tool returns status=error, explain that the connected Notion data source "
                    "returned an error and briefly report the error; do not invent another cause."
                ),
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
