from __future__ import annotations
import json
import requests
from config import OLLAMA_URL, OLLAMA_MODEL


class OllamaProvider:
    def __init__(self, model: str = OLLAMA_MODEL, base_url: str = OLLAMA_URL):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str, image_b64: str | None = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1},
        }

        if image_b64:
            payload["images"] = [image_b64]

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json().get("response", "")
        except requests.exceptions.ConnectionError:
            return json.dumps({"error": "Ollama not running. Start it with: ollama serve"})
        except Exception as e:
            return json.dumps({"error": str(e)})
