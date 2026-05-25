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

COOKIES_FILE = "/tmp/yt_cookies.txt"
TMP_DIR = Path("/tmp/saveit")
TMP_DIR.mkdir(exist_ok=True)

# Write YouTube cookies from env var if present
def setup_cookies():
    cookies = os.environ.get("YOUTUBE_COOKIES", "")
    if cookies and not os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "w") as f:
            f.write(cookies)

setup_cookies()


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


def get_ydl_opts():
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        # Bypass YouTube bot detection without cookies
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "player_skip": ["webpage", "configs"],
            }
        },
        "http_headers": {
            "User-Agent": "com.google.android.youtube/17.36.4 (Linux; U; Android 12; GB) gzip",
        },
    }
    # Also use cookies if available as extra fallback
    cookies = os.environ.get("YOUTUBE_COOKIES", "")
    if cookies:
        with open(COOKIES_FILE, "w") as f:
            f.write(cookies)
        opts["cookiefile"] = COOKIES_FILE
    return opts


@app.get("/")
def root():
    return {"status": "SaveIt API running"}


# Proxy thumbnail images to bypass Instagram CORS
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


# Download + merge Instagram video+audio using ffmpeg, then stream to browser
@app.get("/api/download/instagram")
async def download_instagram(url: str):
    file_id = str(uuid.uuid4())
    out_path = TMP_DIR / f"{file_id}.mp4"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": str(TMP_DIR / f"{file_id}.%(ext)s"),
        # This tells yt-dlp to pick best video+audio and merge with ffmpeg
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }],
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: _download(ydl_opts, url))

        # Find the output file
        actual = None
        for f in TMP_DIR.iterdir():
            if f.stem == file_id and f.suffix == ".mp4":
                actual = f
                break
        # Fallback: any file with that stem
        if not actual:
            for f in TMP_DIR.iterdir():
                if f.stem == file_id:
                    actual = f
                    break

        if not actual or not actual.exists():
            raise HTTPException(status_code=500, detail="Merge failed, file not found")

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
                "Content-Disposition": f'attachment; filename="saveit-reel-{file_id[:8]}.mp4"',
                "Cache-Control": "no-cache",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


def _download(opts, url):
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


@app.post("/api/info")
async def get_info(req: InfoRequest):
    platform = detect_platform(req.url)
    if platform == "unknown":
        raise HTTPException(status_code=400, detail="Only Instagram and YouTube URLs are supported.")

    ydl_opts = get_ydl_opts()

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=False)

        formats = []
        seen = set()

        if platform == "youtube":
            for f in (info.get("formats") or []):
                height = f.get("height")
                vcodec = f.get("vcodec", "none")
                acodec = f.get("acodec", "none")
                furl = f.get("url")
                if not furl:
                    continue
                if vcodec != "none" and acodec != "none" and height:
                    label = f"{height}p"
                    if label not in seen:
                        seen.add(label)
                        formats.append({
                            "format_id": f["format_id"],
                            "label": label,
                            "ext": f.get("ext", "mp4"),
                            "url": furl,
                            "filesize": format_size(f.get("filesize") or f.get("filesize_approx")),
                            "type": "video",
                            "download_via": "direct",
                        })
            formats.sort(key=lambda x: int(x["label"].replace("p", "")), reverse=True)

            for f in (info.get("formats") or []):
                if f.get("vcodec") == "none" and f.get("acodec") != "none" and f.get("url"):
                    formats.append({
                        "format_id": f["format_id"],
                        "label": "Audio Only",
                        "ext": "mp3",
                        "url": f["url"],
                        "filesize": format_size(f.get("filesize")),
                        "type": "audio",
                        "download_via": "direct",
                    })
                    break

            best_url = None
            for f in reversed(info.get("formats") or []):
                if f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("url"):
                    best_url = f["url"]
                    break
            if best_url:
                formats.insert(0, {
                    "format_id": "best",
                    "label": "Best Quality",
                    "ext": "mp4",
                    "url": best_url,
                    "filesize": None,
                    "type": "video",
                    "download_via": "direct",
                })

        elif platform == "instagram":
            # For Instagram, we use our backend merge endpoint for proper audio+video
            import urllib.parse
            merged_url = f"/api/download/instagram?url={urllib.parse.quote(req.url, safe='')}"
            formats.append({
                "format_id": "merged",
                "label": "Best Quality",
                "ext": "mp4",
                "url": merged_url,
                "filesize": None,
                "type": "video",
                "download_via": "proxy",  # tells frontend to use backend URL
            })

        raw_thumb = info.get("thumbnail")
        proxied_thumb = None
        if raw_thumb:
            import urllib.parse
            proxied_thumb = f"/api/thumbnail?url={urllib.parse.quote(raw_thumb, safe='')}"

        return {
            "platform": platform,
            "title": info.get("title") or info.get("description") or "Video",
            "thumbnail": proxied_thumb,
            "duration": info.get("duration"),
            "uploader": info.get("uploader") or info.get("channel") or info.get("owner_username"),
            "view_count": info.get("view_count"),
            "formats": formats,
        }

    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch video: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
