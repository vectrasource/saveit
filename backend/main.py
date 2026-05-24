from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import re

app = FastAPI(title="SaveIt API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your Vercel URL in production
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
                url = f.get("url")
                if not url:
                    continue
                # Combined formats (has both audio+video)
                if vcodec != "none" and acodec != "none" and height:
                    label = f"{height}p"
                    if label not in seen:
                        seen.add(label)
                        formats.append({
                            "format_id": f["format_id"],
                            "label": label,
                            "ext": f.get("ext", "mp4"),
                            "url": url,
                            "filesize": format_size(f.get("filesize") or f.get("filesize_approx")),
                            "type": "video",
                        })
            formats.sort(key=lambda x: int(x["label"].replace("p", "")), reverse=True)

            # Best audio
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

            # Prepend best quality
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
            # Instagram usually has one or two formats
            all_fmts = info.get("formats") or []
            if not all_fmts and info.get("url"):
                all_fmts = [{"url": info["url"], "ext": "mp4", "height": None, "format_id": "best"}]

            for f in all_fmts:
                url = f.get("url")
                if not url:
                    continue
                height = f.get("height")
                label = f"{height}p" if height else "Best Quality"
                if label not in seen:
                    seen.add(label)
                    formats.append({
                        "format_id": f.get("format_id", "best"),
                        "label": label,
                        "ext": f.get("ext", "mp4"),
                        "url": url,
                        "filesize": format_size(f.get("filesize")),
                        "type": "video",
                    })

        return {
            "platform": platform,
            "title": info.get("title") or info.get("description") or "Video",
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader") or info.get("channel") or info.get("owner_username"),
            "view_count": info.get("view_count"),
            "formats": formats,
        }

    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch video: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
