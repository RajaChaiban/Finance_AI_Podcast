from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    """Single-shot chat completion. Pipeline never streams — the script is
    cleaned and validated as a whole before TTS, so partial tokens have no
    use."""

    model: str

    def complete(
        self,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
    ) -> str: ...
