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


@app.get("/api/download/instagram")
async def download_instagram(url: str):
    file_id = str(uuid.uuid4())

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": str(TMP_DIR / f"{file_id}.%(ext)s"),
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        # iPhone compatible codecs
        "postprocessor_args": [
            "-vcodec", "libx264",
            "-acodec", "aac",
            "-movflags", "+faststart",
        ],
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


async def get_youtube_info_rapidapi(url: str):
    """Use RapidAPI YouTube Video and Shorts Downloader by Farhan Ali"""
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
        # Get video details
        details_res = await client.get(
            f"https://youtube-video-and-shorts-downloader.p.rapidapi.com/videodetails.php?id={video_id}",
            headers=headers,
        )
        # Get download streams
        streams_res = await client.get(
            f"https://youtube-video-and-shorts-downloader.p.rapidapi.com/download.php?id={video_id}",
            headers=headers,
        )

    if streams_res.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Could not fetch YouTube streams: {streams_res.text[:200]}")

    streams_data = streams_res.json()
    details_data = details_res.json() if details_res.status_code == 200 else {}

    formats = []
    seen = set()

    # streams_data could be a list or dict
    stream_list = streams_data if isinstance(streams_data, list) else streams_data.get("formats") or streams_data.get("streams") or []

    for fmt in stream_list:
        quality = fmt.get("qualityLabel") or fmt.get("quality") or fmt.get("resolution") or ""
        furl = fmt.get("url") or fmt.get("downloadUrl") or fmt.get("link")
        mime = fmt.get("mimeType") or fmt.get("type") or ""
        has_audio = fmt.get("hasAudio", True)
        has_video = fmt.get("hasVideo", True)

        if not furl or not quality:
            continue

        # Video with audio
        if has_video and has_audio and quality not in seen:
            seen.add(quality)
            formats.append({
                "format_id": str(fmt.get("itag", quality)),
                "label": quality,
                "ext": "mp4",
                "url": furl,
                "filesize": format_size(fmt.get("contentLength") or fmt.get("filesize")),
                "type": "video",
                "download_via": "direct",
            })

    # Sort by quality descending
    def quality_sort(f):
        try:
            return int(f["label"].replace("p","").replace("HD","").split("p")[0].strip())
        except:
            return 0
    formats.sort(key=quality_sort, reverse=True)

    # Audio only
    for fmt in stream_list:
        furl = fmt.get("url") or fmt.get("downloadUrl") or fmt.get("link")
        has_video = fmt.get("hasVideo", True)
        has_audio = fmt.get("hasAudio", True)
        if furl and has_audio and not has_video and "Audio" not in seen:
            seen.add("Audio")
            formats.append({
                "format_id": "audio",
                "label": "Audio Only",
                "ext": "mp3",
                "url": furl,
                "filesize": None,
                "type": "audio",
                "download_via": "direct",
            })
            break

    if not formats:
        raise HTTPException(status_code=400, detail="No downloadable formats found")

    # Get metadata from details or streams
    title = details_data.get("title") or streams_data.get("title") if isinstance(streams_data, dict) else "YouTube Video"
    thumbnail = details_data.get("thumbnail") or streams_data.get("thumbnail") if isinstance(streams_data, dict) else None
    if isinstance(thumbnail, dict):
        thumbnail = thumbnail.get("url")

    return {
        "platform": "youtube",
        "title": title or "YouTube Video",
        "thumbnail": thumbnail,
        "duration": details_data.get("lengthSeconds") or details_data.get("duration"),
        "uploader": details_data.get("author") or details_data.get("channel"),
        "view_count": details_data.get("viewCount"),
        "formats": formats,
    }


@app.post("/api/info")
async def get_info(req: InfoRequest):
    platform = detect_platform(req.url)
    if platform == "unknown":
        raise HTTPException(status_code=400, detail="Only Instagram and YouTube URLs are supported.")

    if platform == "youtube":
        return await get_youtube_info_rapidapi(req.url)

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
