from __future__ import annotations
from typing import Protocol


class LLMProvider(Protocol):
    def generate(self, prompt: str, image_b64: str | None = None) -> str: ...
