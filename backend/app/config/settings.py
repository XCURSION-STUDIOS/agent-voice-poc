from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All provider choices live here; pipeline code consumes only factories."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    transport: str = "webrtc"
    system_prompt: str = Field(
        default=(
            "You are a personal AI assistant in a natural spoken conversation. "
            "Be concise, conversational, and do not use markdown."
        )
    )

    llm_provider: str = "openai"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.6-luna"

    stt_provider: str = "deepgram"
    deepgram_api_key: SecretStr | None = None

    tts_provider: str = "openai"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "marin"
    openai_tts_instructions: str = (
        "Speak in a warm, natural British accent. Conversational, clear, and unhurried."
    )
    deepgram_tts_voice: str = "aura-2-arcas-en"

    min_start_words: int = 2

    def required_secret(self, value: SecretStr | None, name: str) -> str:
        if value is None or not value.get_secret_value():
            raise ValueError(f"{name} is required for the selected provider")
        return value.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()
