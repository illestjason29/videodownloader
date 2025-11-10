"""Pydantic models for TikLoader API."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class VideoFormat(BaseModel):
    """Represents a downloadable format returned by yt_dlp."""

    format_id: str
    ext: str
    format_note: Optional[str]
    resolution: Optional[str]
    fps: Optional[float]
    filesize: Optional[int]
    tbr: Optional[float]
    vcodec: Optional[str]
    acodec: Optional[str]
    preference: Optional[int]


class AudioFormat(BaseModel):
    """Represents an audio-only extraction option."""

    format_id: str
    ext: str
    abr: Optional[float]
    filesize: Optional[int]
    format_note: Optional[str]


class VideoMetadata(BaseModel):
    """Metadata describing the TikTok video requested by the user."""

    id: str
    title: str
    creator: Optional[str]
    description: Optional[str]
    duration: Optional[float]
    thumbnail: Optional[HttpUrl]
    webpage_url: HttpUrl
    formats: List[VideoFormat]
    audio_formats: List[AudioFormat]
    watermark_free_available: bool = False
