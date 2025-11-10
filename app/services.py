"""Service helpers for interacting with yt_dlp."""
from __future__ import annotations

import contextlib
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from fastapi import HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from yt_dlp import YoutubeDL

from .models import AudioFormat, VideoFormat, VideoMetadata


YDL_BASE_OPTS: Dict[str, object] = {
    "quiet": True,
    "skip_download": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "geo_bypass": True,
    "outtmpl": "%(id)s.%(ext)s",
}


def _normalize_resolution(fmt: Dict[str, object]) -> str | None:
    height = fmt.get("height")
    width = fmt.get("width")
    if height and width:
        return f"{int(width)}x{int(height)}"
    if height:
        return f"{int(height)}p"
    return None


def _map_video_format(fmt: Dict[str, object]) -> VideoFormat:
    return VideoFormat(
        format_id=str(fmt.get("format_id")),
        ext=str(fmt.get("ext")),
        format_note=fmt.get("format_note"),
        resolution=_normalize_resolution(fmt),
        fps=fmt.get("fps"),
        filesize=fmt.get("filesize") or fmt.get("filesize_approx"),
        tbr=fmt.get("tbr"),
        vcodec=fmt.get("vcodec"),
        acodec=fmt.get("acodec"),
        preference=fmt.get("preference"),
    )


def _map_audio_format(fmt: Dict[str, object]) -> AudioFormat:
    return AudioFormat(
        format_id=str(fmt.get("format_id")),
        ext=str(fmt.get("ext")),
        abr=fmt.get("abr"),
        filesize=fmt.get("filesize") or fmt.get("filesize_approx"),
        format_note=fmt.get("format_note"),
    )


def _extract_formats(info: Dict[str, object]) -> Tuple[List[VideoFormat], List[AudioFormat], bool]:
    video_formats: List[VideoFormat] = []
    audio_formats: List[AudioFormat] = []
    watermark_free = False

    for fmt in info.get("formats", []):
        if fmt.get("acodec") == "none" and fmt.get("vcodec") and fmt.get("vcodec") != "none":
            video_formats.append(_map_video_format(fmt))
            if "nowatermark" in str(fmt.get("format_note", "")).lower():
                watermark_free = True
        elif fmt.get("vcodec") == "none" and fmt.get("acodec") and fmt.get("acodec") != "none":
            audio_formats.append(_map_audio_format(fmt))

    if info.get("webpage_url_basename"):  # TikTok specific metadata
        watermark_free = watermark_free or info.get("webpage_url_basename", "").endswith("nowm")

    return video_formats, audio_formats, watermark_free


def fetch_video_metadata(url: str) -> VideoMetadata:
    """Fetch metadata for the provided TikTok URL."""

    with YoutubeDL(YDL_BASE_OPTS.copy()) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as exc:  # pragma: no cover - network/yt_dlp errors surfaced to user
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    video_formats, audio_formats, watermark_free = _extract_formats(info)

    return VideoMetadata(
        id=str(info.get("id")),
        title=info.get("title", "TikTok Video"),
        creator=info.get("uploader") or info.get("creator"),
        description=info.get("description"),
        duration=info.get("duration"),
        thumbnail=info.get("thumbnail"),
        webpage_url=info.get("webpage_url") or url,
        formats=video_formats,
        audio_formats=audio_formats,
        watermark_free_available=watermark_free,
    )


def _sanitize_filename(name: str) -> str:
    """Return a filesystem-safe version of the provided filename hint."""

    cleaned = re.sub(r"[\s]+", "_", name.strip())
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "", cleaned)
    cleaned = cleaned.strip("._")
    return cleaned or "download"


def _download_to_temp(
    url: str,
    format_selector: str,
    is_audio: bool = False,
) -> Tuple[Path, str]:
    """Download the requested format to a temporary file and return the path and filename."""

    temp_dir = Path(tempfile.mkdtemp(prefix="tikloader_"))
    filename = temp_dir / "%(title)s.%(ext)s"

    opts: Dict[str, object] = {
        **YDL_BASE_OPTS,
        "skip_download": False,
        "outtmpl": str(filename),
        "format": format_selector,
    }

    if is_audio:
        opts.update(
            {
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "postprocessor_args": ["-ar", "44100"],
            }
        )

    with YoutubeDL(opts) as ydl:
        try:
            result = ydl.extract_info(url, download=True)
        except Exception as exc:  # pragma: no cover - surfaces runtime errors
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    if is_audio:
        expected_ext = "mp3"
    else:
        expected_ext = result.get("ext") or format_selector.split("/")[-1]

    chosen_file: Path | None = None
    for path in temp_dir.iterdir():
        if path.suffix.lower().lstrip(".") == expected_ext.lower():
            chosen_file = path
            break
    if not chosen_file:
        with contextlib.suppress(StopIteration):
            chosen_file = next(iter(temp_dir.iterdir()))
    if not chosen_file:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="Failed to locate downloaded file")

    return chosen_file, result.get("title", chosen_file.name)


def _cleanup_directory(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def stream_download(url: str, format_id: str, filename_hint: str | None = None) -> FileResponse:
    """Return a FileResponse for the requested video format."""

    file_path, title = _download_to_temp(url, format_id)
    base_name = _sanitize_filename(filename_hint or title)
    filename = f"{base_name}.{file_path.suffix.lstrip('.')}"

    return FileResponse(
        path=file_path,
        media_type="video/mp4" if file_path.suffix.lower() == ".mp4" else "application/octet-stream",
        filename=filename,
        background=BackgroundTask(_cleanup_directory, file_path.parent),
    )


def stream_audio(url: str, format_id: str | None, filename_hint: str | None = None) -> FileResponse:
    """Return a FileResponse for an audio-only download."""

    selector = format_id or "bestaudio/best"
    file_path, title = _download_to_temp(url, selector, is_audio=True)
    base_name = _sanitize_filename(filename_hint or title)
    filename = f"{base_name}.mp3"

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename,
        background=BackgroundTask(_cleanup_directory, file_path.parent),
    )
