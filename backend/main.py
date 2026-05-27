from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
import yt_dlp
import re
import httpx
import os
import urllib.parse
import asyncio
import uuid
import subprocess
from pathlib import Path

app = FastAPI(title="SaveIt API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")
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


@app.get("/api/proxy")
async def proxy_video(url: str, filename: str = "saveit-video.mp4"):
    """
    Proxy a CDN video URL through our server so browser downloads
    it as a file instead of playing it inline. Keeps memory low
    by streaming in chunks.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.instagram.com/",
        }
        client = httpx.AsyncClient(follow_redirects=True, timeout=60)
        req = client.stream("GET", url, headers=headers)
        response = await req.__aenter__()

        async def stream_and_close():
            try:
                async for chunk in response.aiter_bytes(65536):
                    yield chunk
            finally:
                await req.__aexit__(None, None, None)
                await client.aclose()

        return StreamingResponse(
            stream_and_close(),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")


def get_instagram_info(url: str):
    """Instagram via yt-dlp — grab best combined stream"""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats_list = info.get("formats", [])

        # Priority 1: format with BOTH video and audio
        combined = []
        for f in formats_list:
            vcodec = f.get("vcodec", "none")
            acodec = f.get("acodec", "none")
            if vcodec != "none" and acodec != "none" and f.get("url"):
                combined.append(f)

        # Sort by height descending
        combined.sort(key=lambda f: f.get("height") or 0, reverse=True)

        if combined:
            best = combined[0]
        elif formats_list:
            # Fallback — any format with url
            best = next((f for f in reversed(formats_list) if f.get("url")), None)
        else:
            best = None

        if not best and info.get("url"):
            best = {"url": info["url"], "ext": "mp4", "height": None}

        if not best:
            raise HTTPException(status_code=400, detail="No downloadable format found")

        raw_thumb = info.get("thumbnail")
        proxied_thumb = None
        if raw_thumb:
            proxied_thumb = f"/api/thumbnail?url={urllib.parse.quote(raw_thumb, safe='')}"

        # Use proxy endpoint so mobile browsers download instead of play inline
        video_url = best["url"]
        proxy_url = f"/api/proxy?url={urllib.parse.quote(video_url, safe='')}&filename=saveit-instagram.mp4"

        return {
            "platform": "instagram",
            "title": info.get("title") or info.get("description") or "Instagram Video",
            "thumbnail": proxied_thumb,
            "duration": info.get("duration"),
            "uploader": info.get("uploader") or info.get("owner_username"),
            "view_count": info.get("view_count"),
            "formats": [{
                "format_id": "best",
                "label": "Best Quality",
                "ext": best.get("ext", "mp4"),
                "url": proxy_url,
                "filesize": format_size(best.get("filesize")),
                "type": "video",
                "download_via": "proxy",
            }],
        }

    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch video: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


async def get_youtube_info(url: str):
    """YouTube via RapidAPI"""
    if not RAPIDAPI_KEY:
        raise HTTPException(status_code=500, detail="YouTube API not configured")

    vid_match = re.search(r"(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})", url)
    if not vid_match:
        raise HTTPException(status_code=400, detail="Could not extract YouTube video ID")
    video_id = vid_match.group(1)

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "youtube-video-and-shorts-downloader.p.rapidapi.com",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(
            f"https://youtube-video-and-shorts-downloader.p.rapidapi.com/download.php?id={video_id}",
            headers=headers,
        )

    if res.status_code != 200:
        raise HTTPException(status_code=400, detail="Could not fetch YouTube video")

    data = res.json()
    results = data.get("results", [])

    formats = []
    seen = set()

    audio_stream = next((r for r in results if r.get("has_audio") and "audio" in r.get("mime", "")), None)
    video_streams = [r for r in results if "video" in r.get("mime", "") and not r.get("has_audio")]

    quality_order = ["720p", "480p", "360p", "240p", "144p"]

    for quality in quality_order:
        match = next((v for v in video_streams if v.get("quality") == quality), None)
        if match and quality not in seen:
            seen.add(quality)
            # Proxy through our server so it downloads properly on mobile
            proxy_url = f"/api/proxy?url={urllib.parse.quote(match['url'], safe='')}&filename=saveit-youtube-{quality}.mp4"
            formats.append({
                "format_id": quality,
                "label": f"{quality} (Video only)",
                "ext": "mp4",
                "url": proxy_url,
                "filesize": None,
                "type": "video",
                "download_via": "proxy",
            })

    # Audio only — proxy for proper download
    if audio_stream:
        proxy_url = f"/api/proxy?url={urllib.parse.quote(audio_stream['url'], safe='')}&filename=saveit-youtube-audio.m4a"
        formats.append({
            "format_id": "audio",
            "label": "Audio Only (M4A)",
            "ext": "m4a",
            "url": proxy_url,
            "filesize": None,
            "type": "audio",
            "download_via": "proxy",
        })

    if not formats:
        raise HTTPException(status_code=400, detail="No downloadable formats found")

    return {
        "platform": "youtube",
        "title": data.get("title", "YouTube Video"),
        "thumbnail": data.get("thumbnail", f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"),
        "duration": data.get("duration"),
        "uploader": data.get("author"),
        "view_count": None,
        "formats": formats,
    }


@app.post("/api/info")
async def get_info(req: InfoRequest):
    platform = detect_platform(req.url)
    if platform == "unknown":
        raise HTTPException(status_code=400, detail="Only Instagram and YouTube URLs are supported.")

    if platform == "youtube":
        return await get_youtube_info(req.url)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: get_instagram_info(req.url))
