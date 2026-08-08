from pathlib import Path

BASE_DIR = Path(__file__).parent

# ─── LLM Model ───
# Change this ONE string to switch providers. Examples:
#   "ollama/minicpm-v"              — local Ollama (free, slower)
#   "claude-sonnet-4-20250514"               — Anthropic Claude (best quality)
#   "gpt-4o"                        — OpenAI GPT-4o
#   "gemini/gemini-2.5-flash"       — Google Gemini (cheap + fast)
#   "together_ai/meta-llama/..."    — Together AI
#   "groq/llama-3.1-70b-versatile"  — Groq (fast, free tier)
LLM_MODEL = "gemini/gemini-3.1-flash-lite"

# ML Models (local, free)
CLIP_MODEL_NAME = "ViT-B-32"
CLIP_PRETRAINED = "openai"

# Database
SQLITE_PATH = BASE_DIR / "scenepoint.db"

# Rate Limiting
RATE_LIMIT_PER_DAY = 50  # set to 5 for production

# Caching
CACHE_TIMESTAMP_TOLERANCE = 10

# Geocoding
NOMINATIM_USER_AGENT = "scenepoint-mvp/0.1"

# API
import os
API_HOST = "0.0.0.0"
API_PORT = int(os.environ.get("PORT", 8000))
