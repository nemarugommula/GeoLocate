"""
Multi-provider LLM support via LiteLLM.
Supports Claude, GPT-4o, Gemini, Ollama, Together, and 100+ others.
Change the model string in config.py — no code changes needed.
"""
from __future__ import annotations
import json
import litellm
from config import LLM_MODEL

litellm.drop_params = True


def generate(prompt: str, image_b64: str | None = None) -> str:
    messages = []

    if image_b64:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
            ],
        })
    else:
        messages.append({"role": "user", "content": prompt})

    try:
        response = litellm.completion(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=1000,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        return json.dumps({"error": str(e)})
