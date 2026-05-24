from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import yt_dlp
import re
import httpx

app = FastAPI(title="SaveIt API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# Proxy thumbnail images to bypass Instagram CORS restrictions
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


@app.post("/api/info")
async def get_info(req: InfoRequest):
    platform = detect_platform(req.url)
    if platform == "unknown":
        raise HTTPException(status_code=400, detail="Only Instagram and YouTube URLs are supported.")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

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
                        })
            formats.sort(key=lambda x: int(x["label"].replace("p", "")), reverse=True)

            # Best audio only
            for f in (info.get("formats") or []):
                if f.get("vcodec") == "none" and f.get("acodec") != "none" and f.get("url"):
                    formats.append({
                        "format_id": f["format_id"],
                        "label": "Audio Only",
                        "ext": "mp3",
                        "url": f["url"],
                        "filesize": format_size(f.get("filesize")),
                        "type": "audio",
                    })
                    break

            # Prepend best combined quality
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
                })

        elif platform == "instagram":
            all_fmts = info.get("formats") or []

            # Filter: only keep formats that have video (vcodec not none)
            # Instagram sometimes returns audio-only streams — skip those
            video_fmts = [
                f for f in all_fmts
                if f.get("vcodec", "none") != "none" and f.get("url")
            ]

            # Fallback: if no vcodec info available, take all formats with a url
            if not video_fmts:
                video_fmts = [f for f in all_fmts if f.get("url")]

            # Further fallback: use top-level url
            if not video_fmts and info.get("url"):
                video_fmts = [{"url": info["url"], "ext": "mp4", "height": None, "format_id": "best", "vcodec": "h264"}]

            # Pick best (highest height or last in list)
            video_fmts_sorted = sorted(
                video_fmts,
                key=lambda f: f.get("height") or 0,
                reverse=True
            )

            for f in video_fmts_sorted:
                furl = f.get("url")
                if not furl:
                    continue
                height = f.get("height")
                label = f"{height}p" if height else "Best Quality"
                if label not in seen:
                    seen.add(label)
                    formats.append({
                        "format_id": f.get("format_id", "best"),
                        "label": label,
                        "ext": f.get("ext", "mp4"),
                        "url": furl,
                        "filesize": format_size(f.get("filesize")),
                        "type": "video",
                    })

        # Proxy the thumbnail URL through our server to bypass CORS
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
