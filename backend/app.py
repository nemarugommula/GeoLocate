"""
Scenera API — deployed as a Gradio Space with FastAPI mounted.
Gradio handles the hosting, FastAPI handles the API routes.
"""
import gradio as gr
from main import app as fastapi_app

# Minimal Gradio UI (required for HF Spaces to recognize it)
with gr.Blocks(title="Scenera API") as demo:
    gr.Markdown("# Scenera API")
    gr.Markdown("AI-powered location discovery from YouTube video frames.")
    gr.Markdown("This Space serves the Scenera API. Use the Chrome extension to interact with it.")
    gr.Markdown("### Endpoints")
    gr.Markdown("- `POST /lookup` — Find location from a video frame")
    gr.Markdown("- `GET /history` — Get user's past lookups")
    gr.Markdown("- `POST /feedback` — Submit feedback")
    gr.Markdown("- `GET /health` — Health check")

# Mount FastAPI inside Gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/")
