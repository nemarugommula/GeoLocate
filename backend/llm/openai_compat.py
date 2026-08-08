"""Stub for Claude / OpenAI API integration. Swap in by changing LLM_PROVIDER in config.py."""
from __future__ import annotations


class OpenAICompatProvider:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str, image_b64: str | None = None) -> str:
        raise NotImplementedError("OpenAI/Claude provider not yet implemented. Use Ollama for now.")
