from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import yt_dlp
import re
import httpx
import os
import urllib.parse

app = FastAPI(title="SaveIt API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")


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


async def get_youtube_info(url: str):
    """YouTube via RapidAPI — direct CDN links, no server merging"""
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

    # Audio stream
    audio_stream = next((r for r in results if r.get("has_audio") and "audio" in r.get("mime", "")), None)

    # Video streams — send direct to browser
    quality_order = ["1080p", "720p", "480p", "360p", "240p", "144p"]
    video_streams = [r for r in results if "video" in r.get("mime", "") and not r.get("has_audio")]

    for quality in quality_order:
        match = next((v for v in video_streams if v.get("quality") == quality), None)
        if match and quality not in seen:
            seen.add(quality)
            formats.append({
                "format_id": quality,
                "label": f"{quality} (Video)",
                "ext": "mp4",
                "url": match["url"],
                "filesize": None,
                "type": "video",
                "download_via": "direct",
            })

    # Audio only
    if audio_stream:
        formats.append({
            "format_id": "audio",
            "label": "Audio Only (M4A)",
            "ext": "m4a",
            "url": audio_stream["url"],
            "filesize": None,
            "type": "audio",
            "download_via": "direct",
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


def get_instagram_info(url: str):
    """Instagram via yt-dlp — best single stream, no merging"""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        # Pick best format that already has video+audio combined
        "format": "best[ext=mp4]/best",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Get the direct URL of the best combined format
        formats_list = info.get("formats", [])

        # Find best format that has both video and audio
        best = None
        for f in reversed(formats_list):
            vcodec = f.get("vcodec", "none")
            acodec = f.get("acodec", "none")
            if vcodec != "none" and acodec != "none" and f.get("url"):
                best = f
                break

        # Fallback to any format with a URL
        if not best:
            for f in reversed(formats_list):
                if f.get("url"):
                    best = f
                    break

        # Last fallback — top level URL
        if not best and info.get("url"):
            best = {"url": info["url"], "ext": "mp4", "height": None}

        if not best:
            raise HTTPException(status_code=400, detail="No downloadable format found")

        raw_thumb = info.get("thumbnail")
        proxied_thumb = None
        if raw_thumb:
            proxied_thumb = f"/api/thumbnail?url={urllib.parse.quote(raw_thumb, safe='')}"

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
                "url": best["url"],
                "filesize": format_size(best.get("filesize")),
                "type": "video",
                "download_via": "direct",
            }],
        }

    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch video: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/api/info")
async def get_info(req: InfoRequest):
    platform = detect_platform(req.url)
    if platform == "unknown":
        raise HTTPException(status_code=400, detail="Only Instagram and YouTube URLs are supported.")

    if platform == "youtube":
        return await get_youtube_info(req.url)

    # Instagram runs in thread to not block event loop
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: get_instagram_info(req.url))
