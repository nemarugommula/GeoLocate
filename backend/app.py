"""
Scenera API — HF Spaces entry point.
Gradio UI + FastAPI API mounted together.
"""
import gradio as gr
import uvicorn

# Import FastAPI app (loads ML models on startup)
from main import app as fastapi_app

# Minimal Gradio UI
with gr.Blocks(title="Scenera API") as demo:
    gr.Markdown("# 📍 Scenera API")
    gr.Markdown("AI-powered location discovery from YouTube video frames.")
    gr.Markdown("Use the Scenera Chrome extension to interact with this API.")
    with gr.Accordion("API Endpoints", open=False):
        gr.Markdown("""
        - `POST /lookup` — Find location from a video frame
        - `GET /history` — Get user's past lookups  
        - `POST /feedback` — Submit feedback
        - `GET /health` — Health check
        """)

# Mount Gradio inside FastAPI
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
