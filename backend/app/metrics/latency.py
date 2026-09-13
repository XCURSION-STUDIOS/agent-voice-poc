"""Session-level timing primitives, deliberately independent of any AI provider."""

from dataclasses import dataclass, field
from time import perf_counter

from loguru import logger


@dataclass
class VoiceLatency:
    marks: dict[str, float] = field(default_factory=dict)

    def mark(self, name: str) -> None:
        self.marks.setdefault(name, perf_counter())

    def milliseconds(self, start: str, end: str) -> float | None:
        if start not in self.marks or end not in self.marks:
            return None
        return (self.marks[end] - self.marks[start]) * 1000

    def log_first_response(self) -> None:
        logger.info(
            "[VOICE] STT finalization={}ms | LLM TTFT={}ms | TTS first audio={}ms | "
            "end-to-end={}ms",
            _show(self.milliseconds("user_stop", "stt_final")),
            _show(self.milliseconds("stt_final", "llm_first_token")),
            _show(self.milliseconds("llm_first_token", "tts_first_audio")),
            _show(self.milliseconds("user_stop", "browser_first_audio")),
        )


def _show(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.0f}"
