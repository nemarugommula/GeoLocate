from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import API_HOST, API_PORT, LLM_MODEL
from database import get_connection, init_db
from pipeline.clip_filter import load_clip
from pipeline.geoclip_predict import load_geoclip
from routers import lookup, history, feedback


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load ML models once
    print("Loading CLIP model...")
    clip_model, clip_preprocess, clip_text_features = load_clip()
    app.state.clip_model = clip_model
    app.state.clip_preprocess = clip_preprocess
    app.state.clip_text_features = clip_text_features
    print("CLIP loaded.")

    print("Loading GeoCLIP model...")
    app.state.geoclip_model = load_geoclip()
    print("GeoCLIP loaded.")

    print(f"LLM provider: {LLM_MODEL} (via LiteLLM)")

    # Init database
    conn = get_connection()
    init_db(conn)
    conn.close()
    print("Database ready.")

    print(f"\nScenera API running at http://{API_HOST}:{API_PORT}")
    print("Endpoints:")
    print("  POST /lookup     — Find location from a video frame")
    print("  GET  /history    — Get user's past lookups")
    print("  POST /feedback   — Submit thumbs up/down")
    print("  GET  /health     — Health check\n")

    yield

    # Shutdown
    print("Shutting down Scenera API.")


app = FastAPI(title="Scenera API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lookup.router)
app.include_router(history.router)
app.include_router(feedback.router)


@app.get("/health")
def health():
    return {"status": "ok", "models": ["clip", "geoclip", "ollama"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
