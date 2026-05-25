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


@app.get("/api/debug/youtube")
async def debug_youtube(video_id: str = "zjwXf-L5a-w"):
    """Debug endpoint to see raw RapidAPI response"""
    if not RAPIDAPI_KEY:
        return {"error": "No RAPIDAPI_KEY set"}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "youtube-video-and-shorts-downloader.p.rapidapi.com",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        streams = await client.get(
            f"https://youtube-video-and-shorts-downloader.p.rapidapi.com/download.php?id={video_id}",
            headers=headers,
        )
        details = await client.get(
            f"https://youtube-video-and-shorts-downloader.p.rapidapi.com/videodetails.php?id={video_id}",
            headers=headers,
        )
    return {
        "streams_status": streams.status_code,
        "streams_data": streams.json() if streams.status_code == 200 else streams.text,
        "details_status": details.status_code,
        "details_data": details.json() if details.status_code == 200 else details.text,
    }


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


@app.get("/api/download/youtube")
async def download_youtube(video_url: str, audio_url: str, quality: str = "720p"):
    """Merge YouTube video+audio streams and serve as mp4"""
    file_id = str(uuid.uuid4())
    video_path = TMP_DIR / f"{file_id}_video.mp4"
    audio_path = TMP_DIR / f"{file_id}_audio.m4a"
    output_path = TMP_DIR / f"{file_id}_out.mp4"

    try:
        # Download video and audio streams in parallel
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            v_res, a_res = await asyncio.gather(
                client.get(video_url),
                client.get(audio_url),
            )

        with open(video_path, "wb") as f:
            f.write(v_res.content)
        with open(audio_path, "wb") as f:
            f.write(a_res.content)

        # Merge with ffmpeg — re-encode for compatibility
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            "-crf", "23",
            "-movflags", "+faststart",
            str(output_path)
        ]
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: __import__('subprocess').run(cmd, check=True, capture_output=True))

        # Cleanup input files
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)

        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Merge failed")

        def iter_file():
            with open(output_path, "rb") as f:
                while chunk := f.read(1024 * 64):
                    yield chunk
            output_path.unlink(missing_ok=True)

        return StreamingResponse(
            iter_file(),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="saveit-yt-{quality}-{file_id[:8]}.mp4"',
                "Cache-Control": "no-cache",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        for p in [video_path, audio_path, output_path]:
            try: p.unlink()
            except: pass
        raise HTTPException(status_code=500, detail=f"YouTube download failed: {str(e)}")


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
        streams_res = await client.get(
            f"https://youtube-video-and-shorts-downloader.p.rapidapi.com/download.php?id={video_id}",
            headers=headers,
        )

    if streams_res.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Could not fetch YouTube streams: {streams_res.text[:200]}")

    data = streams_res.json()
    results = data.get("results", [])

    # Separate video-only and audio-only streams
    video_streams = [r for r in results if r.get("mime", "").startswith("video/") and not r.get("has_audio", False)]
    audio_streams = [r for r in results if r.get("has_audio", False) and r.get("mime", "").startswith("audio/")]

    # Get best audio stream URL for merging
    audio_url = audio_streams[0]["url"] if audio_streams else None

    # Build format list — each video quality paired with audio via backend merge
    formats = []
    seen = set()
    quality_order = ["2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]

    for quality in quality_order:
        matching = [v for v in video_streams if v.get("quality") == quality]
        if matching and quality not in seen and audio_url:
            seen.add(quality)
            import urllib.parse
            video_url_enc = urllib.parse.quote(matching[0]["url"], safe="")
            audio_url_enc = urllib.parse.quote(audio_url, safe="")
            merge_url = f"/api/download/youtube?video_url={video_url_enc}&audio_url={audio_url_enc}&quality={quality}"
            formats.append({
                "format_id": quality,
                "label": quality,
                "ext": "mp4",
                "url": merge_url,
                "filesize": None,
                "type": "video",
                "download_via": "proxy",
            })

    # Audio only
    if audio_streams:
        formats.append({
            "format_id": "audio",
            "label": "Audio Only",
            "ext": "mp3",
            "url": audio_streams[0]["url"],
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
