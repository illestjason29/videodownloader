"""FastAPI entry point for the TikLoader application."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .models import VideoMetadata
from .services import fetch_video_metadata, stream_audio, stream_download

app = FastAPI(title="TikLoader", description="TikTok video downloader API")

# Allow browser clients hosted elsewhere during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    """Serve the single page application."""

    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.post("/api/metadata", response_model=VideoMetadata)
def get_metadata(url: Annotated[str, Query(..., description="TikTok video URL")]) -> VideoMetadata:
    """Return metadata and available formats for the provided TikTok URL."""

    return fetch_video_metadata(url)


@app.get("/api/download")
def download_video(
    url: Annotated[str, Query(..., description="TikTok video URL")],
    format_id: Annotated[str, Query(..., description="Format identifier to download")],
    filename: Annotated[str | None, Query(None, description="Optional filename hint")] = None,
) -> FileResponse:
    """Download the TikTok video in the requested format."""

    return stream_download(url, format_id, filename)


@app.get("/api/audio")
def download_audio(
    url: Annotated[str, Query(..., description="TikTok video URL")],
    format_id: Annotated[str | None, Query(None, description="Optional audio format identifier")] = None,
    filename: Annotated[str | None, Query(None, description="Optional filename hint")] = None,
) -> FileResponse:
    """Download the TikTok video's audio as MP3."""

    return stream_audio(url, format_id, filename)
