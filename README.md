# TikLoader

TikLoader is a minimalist TikTok video downloader that lets you paste any TikTok link and grab the
video or audio in a variety of formats—no account needed.

## Features

- 🔗 **Paste & Download** – drop in any TikTok URL to preview metadata and start downloading.
- 🚫 **No Watermarks (when available)** – highlights watermark-free sources so you can pick the
  cleanest version.
- 🎥 **Multiple Resolutions** – choose from HD and SD options exposed by TikTok/yt-dlp.
- 🎧 **Audio Extraction** – one click to convert to MP3 for offline listening.
- ⚡ **Fast & Lightweight** – built with FastAPI and vanilla JS for speedy performance.

## Getting Started

1. Install dependencies (Python 3.11+ recommended):

   ```bash
   pip install -r requirements.txt
   ```

2. Launch the development server:

   ```bash
   uvicorn app.main:app --reload
   ```

3. Open [http://localhost:8000](http://localhost:8000) and paste a TikTok URL to explore available
   downloads.

> **Note:** TikTok downloading relies on `yt-dlp` and `ffmpeg`. Ensure `ffmpeg` is available on your
> system for MP3 conversions. Respect TikTok's terms and content creator rights when downloading.

## Project Structure

```
app/
├── __init__.py
├── main.py             # FastAPI entry point and routes
├── models.py           # Pydantic response models
├── services.py         # yt-dlp integration helpers
└── static/
    ├── index.html      # Minimal single-page UI
    ├── script.js       # Front-end interactions and API calls
    └── styles.css      # Styling for the downloader
requirements.txt        # Python dependencies
```

## Roadmap Ideas

- Queueing multiple downloads at once
- Usage analytics dashboard (self-hosted)
- Localization for additional languages
