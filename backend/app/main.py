"""
YT Automation Backend - FastAPI Application

Local ML-powered YouTube video analysis and Shorts generation.

Tech stack:
- Whisper: Speech-to-text transcription (local, free)
- CLIP: Visual frame analysis (local, free)
- Ollama + LLaMA/Mistral: Content analysis with local LLM
- librosa: Audio energy and feature analysis
- PySceneDetect: Scene boundary detection
- FFmpeg: Video processing and Shorts generation
- SQLite: Persistent storage

No paid APIs. Everything runs locally.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .database import init_db
from .routers import videos, analysis, channel, templates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")

    # Check available ML tools
    _check_dependencies()

    yield

    logger.info("Shutting down...")


def _check_dependencies():
    """Check which ML dependencies are available and log status."""
    deps = {
        "whisper": "openai-whisper (speech recognition)",
        "scenedetect": "PySceneDetect (scene detection)",
        "librosa": "librosa (audio analysis)",
        "transformers": "transformers (CLIP visual analysis)",
        "ollama": "Ollama client (local LLM)",
    }

    for module, description in deps.items():
        try:
            __import__(module)
            logger.info(f"  ✓ {description} - available")
        except ImportError:
            logger.warning(f"  ✗ {description} - NOT available (install for full functionality)")

    # Check FFmpeg
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        logger.info("  ✓ FFmpeg - available")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("  ✗ FFmpeg - NOT available (required for video processing)")

    # Check yt-dlp
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, timeout=5)
        logger.info("  ✓ yt-dlp - available")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("  ✗ yt-dlp - NOT available (required for YouTube downloads)")


app = FastAPI(
    title="YT Automation API",
    description="Local ML-powered YouTube video analysis and Shorts generation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated outputs as static files
outputs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(outputs_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)

app.mount("/static/outputs", StaticFiles(directory=outputs_dir), name="outputs")
app.mount("/static/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include routers
app.include_router(videos.router)
app.include_router(analysis.router)
app.include_router(channel.router)
app.include_router(templates.router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "yt-automation-api"}
