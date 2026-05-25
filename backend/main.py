from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
import yt_dlp
import re
import httpx
import os
import uuid
import asyncio
from pathlib import Path

app = FastAPI(title="SaveIt API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TMP_DIR = Path("/tmp/saveit")
TMP_DIR.mkdir(exist_ok=True)


class InfoRequest(BaseModel):
    url: str


def detect_platform(url: str) -> str:
    if re.search(r"instagram\.com|instagr\.am", url):
        return "instagram"
    if re.search(r"youtube\.com|youtu\.be", url):
        return "youtube"
    return "unknown"


def format_size(size):
    if not size:
        return None
    if size > 1e9:
        return f"{size/1e9:.1f} GB"
    if size > 1e6:
        return f"{size/1e6:.1f} MB"
    return f"{size/1e3:.0f} KB"


@app.get("/")
def root():
    return {"status": "SaveIt API running"}


@app.get("/api/thumbnail")
async def proxy_thumbnail(url: str):
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.instagram.com/",
            }
            r = await client.get(url, headers=headers)
            return Response(
                content=r.content,
                media_type=r.headers.get("content-type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=3600"},
            )
    except Exception:
        raise HTTPException(status_code=502, detail="Could not fetch thumbnail")


@app.get("/api/download/instagram")
async def download_instagram(url: str):
    file_id = str(uuid.uuid4())

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": str(TMP_DIR / f"{file_id}.%(ext)s"),
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: _ydl_download(ydl_opts, url))

        actual = None
        for f in TMP_DIR.iterdir():
            if f.stem == file_id:
                actual = f
                break

        if not actual or not actual.exists():
            raise HTTPException(status_code=500, detail="Download failed")

        def iter_file():
            with open(actual, "rb") as f:
                while chunk := f.read(1024 * 64):
                    yield chunk
            try:
                actual.unlink()
            except Exception:
                pass

        return StreamingResponse(
            iter_file(),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="saveit-{file_id[:8]}.mp4"',
                "Cache-Control": "no-cache",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


def _ydl_download(opts, url):
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


def get_youtube_info(url: str):
    """Use pytubefix with PO Token support"""
    try:
        from pytubefix import YouTube
        from pytubefix.cli import on_progress

        # Use WEB client with PO token — bypasses bot detection
        yt = YouTube(
            url,
            client="WEB",
            use_oauth=False,
            allow_oauth_cache=False,
        )

        formats = []
        seen = set()

        # Progressive streams have video+audio combined
        streams = yt.streams.filter(progressive=True, file_extension='mp4')
        for stream in sorted(streams, key=lambda s: int((s.resolution or '0p').replace('p','')), reverse=True):
            label = stream.resolution or "Unknown"
            if label not in seen:
                seen.add(label)
                formats.append({
                    "format_id": str(stream.itag),
                    "label": label,
                    "ext": "mp4",
                    "url": stream.url,
                    "filesize": format_size(stream.filesize_approx),
                    "type": "video",
                    "download_via": "direct",
                })

        # Fallback to highest resolution
        if not formats:
            stream = yt.streams.get_highest_resolution()
            if stream:
                formats.append({
                    "format_id": str(stream.itag),
                    "label": stream.resolution or "Best",
                    "ext": "mp4",
                    "url": stream.url,
                    "filesize": format_size(stream.filesize_approx),
                    "type": "video",
                    "download_via": "direct",
                })

        # Audio only
        audio = yt.streams.filter(only_audio=True).order_by('abr').last()
        if audio:
            formats.append({
                "format_id": f"audio_{audio.itag}",
                "label": "Audio Only",
                "ext": "mp3",
                "url": audio.url,
                "filesize": format_size(audio.filesize_approx),
                "type": "audio",
                "download_via": "direct",
            })

        return {
            "platform": "youtube",
            "title": yt.title,
            "thumbnail": yt.thumbnail_url,
            "duration": yt.length,
            "uploader": yt.author,
            "view_count": yt.views,
            "formats": formats,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch YouTube video: {str(e)}")


@app.post("/api/info")
async def get_info(req: InfoRequest):
    platform = detect_platform(req.url)
    if platform == "unknown":
        raise HTTPException(status_code=400, detail="Only Instagram and YouTube URLs are supported.")

    if platform == "youtube":
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: get_youtube_info(req.url))

    # Instagram via yt-dlp
    ydl_opts = {"quiet": True, "no_warnings": True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=False)

        import urllib.parse
        merged_url = f"/api/download/instagram?url={urllib.parse.quote(req.url, safe='')}"

        raw_thumb = info.get("thumbnail")
        proxied_thumb = None
        if raw_thumb:
            proxied_thumb = f"/api/thumbnail?url={urllib.parse.quote(raw_thumb, safe='')}"

        return {
            "platform": "instagram",
            "title": info.get("title") or info.get("description") or "Video",
            "thumbnail": proxied_thumb,
            "duration": info.get("duration"),
            "uploader": info.get("uploader") or info.get("owner_username"),
            "view_count": info.get("view_count"),
            "formats": [{
                "format_id": "merged",
                "label": "Best Quality",
                "ext": "mp4",
                "url": merged_url,
                "filesize": None,
                "type": "video",
                "download_via": "proxy",
            }],
        }

    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch video: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
