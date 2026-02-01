"""Gallery and content serving routes."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
import os
import json
import logging
import zipfile
import tempfile
import mimetypes

from app.utils.image_files import list_images

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gallery", tags=["Gallery"])

APPROVAL_STATUS_FILE = "data/approval_status.json"


def load_approval_status() -> dict:
    try:
        if os.path.exists(APPROVAL_STATUS_FILE):
            with open(APPROVAL_STATUS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load approval status: {e}")
    return {}


def save_approval_status(status: dict):
    try:
        os.makedirs(os.path.dirname(APPROVAL_STATUS_FILE), exist_ok=True)
        with open(APPROVAL_STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save approval status: {e}")


@router.get("")
async def gallery_redirect():
    """Legacy gallery route - redirects to unified dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=301)


@router.get("/images/{influencer}")
async def get_gallery_images(influencer: str, source: str = Query(default="all")):
    """
    Get gallery images for an influencer.
    
    Args:
        influencer: Influencer ID (luna_vale, starbright_monroe)
        source: Filter by source - "all", "raw", "generated", "final", "research"
    """
    influencer_key = influencer.lower().replace(" ", "_")
    
    images = []
    
    final_folder = Path(f"content/final/{influencer_key}")
    final_filenames = set()
    if final_folder.exists():
        final_filenames = {f.name for f in list_images(final_folder)}
    
    if source in ["all", "generated"]:
        generated_folder = Path(f"content/generated/{influencer_key}")
        if generated_folder.exists():
            for file in list_images(generated_folder):
                if file.name in final_filenames:
                    continue
                stat = file.stat()
                images.append({
                    "filename": file.name,
                    "path": str(file),
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "mtime": stat.st_mtime,
                    "source": "generated"
                })
    
    if source in ["all", "seedream"]:
        seedream_folder = Path("content/seedream4_output")
        if seedream_folder.exists():
            for file in list_images(seedream_folder):
                if file.name in final_filenames:
                    continue
                stat = file.stat()
                images.append({
                    "filename": file.name,
                    "path": str(file),
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "mtime": stat.st_mtime,
                    "source": "seedream"
                })
    
    if source in ["all", "venice"]:
        venice_folder = Path("content/venice_output")
        if venice_folder.exists():
            for file in list_images(venice_folder):
                if file.name in final_filenames:
                    continue
                stat = file.stat()
                images.append({
                    "filename": file.name,
                    "path": str(file),
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "mtime": stat.st_mtime,
                    "source": "venice"
                })
    
    if source in ["all", "raw"]:
        raw_folder = Path(f"content/raw/{influencer_key}")
        if raw_folder.exists():
            for file in list_images(raw_folder):
                if file.name in final_filenames:
                    continue
                stat = file.stat()
                images.append({
                    "filename": file.name,
                    "path": str(file),
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "mtime": stat.st_mtime,
                    "source": "raw"
                })
    
    if source in ["all", "final"]:
        if final_folder.exists():
            for file in list_images(final_folder):
                stat = file.stat()
                images.append({
                    "filename": file.name,
                    "path": str(file),
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "mtime": stat.st_mtime,
                    "source": "final"
                })
    
    images.sort(key=lambda x: x["mtime"], reverse=True)
    
    for img in images:
        del img["mtime"]
    
    approval_status = load_approval_status()
    
    for img in images:
        if img["path"].startswith("content/final/"):
            approval_status[img["path"]] = "final"
    
    return {"images": images[:50], "approval_status": approval_status}


def validate_content_path(path: str) -> Path:
    """Validate that a path is within the content directory, preventing path traversal."""
    content_root = Path("content").resolve()
    file_path = Path(path).resolve()
    
    if not str(file_path).startswith(str(content_root)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return file_path


@router.get("/image/{path:path}")
async def serve_gallery_image(path: str):
    file_path = validate_content_path(path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    media_type, _ = mimetypes.guess_type(str(file_path))
    if not media_type:
        media_type = "application/octet-stream"

    return FileResponse(
        file_path,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=3600"}
    )


@router.get("/download/{path:path}")
async def download_gallery_file(path: str):
    """Download a single image or video file."""
    file_path = validate_content_path(path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    suffix = file_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
    }
    media_type = media_types.get(suffix, "application/octet-stream")
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=file_path.name,
        headers={"Content-Disposition": f"attachment; filename={file_path.name}"}
    )


@router.get("/videos/{influencer}")
async def get_gallery_videos(influencer: str, source: str = Query(default="all")):
    """
    Get gallery videos for an influencer.
    
    Args:
        influencer: Influencer ID (luna_vale, starbright_monroe)
        source: Filter by source - "all", "omnihuman", "loops"
    """
    influencer_key = influencer.lower().replace(" ", "_")
    
    videos = []
    
    video_folders = {
        "omnihuman": Path("content/videos/omnihuman"),
        "loops": Path("content/loops"),
    }
    
    for folder_name, folder_path in video_folders.items():
        if source not in ["all", folder_name]:
            continue
        if not folder_path.exists():
            continue
        
        for file in folder_path.glob("*.mp4"):
            stat = file.stat()
            videos.append({
                "filename": file.name,
                "path": str(file),
                "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "mtime": stat.st_mtime,
                "source": folder_name
            })
    
    videos.sort(key=lambda x: x["mtime"], reverse=True)
    
    for v in videos:
        del v["mtime"]
    
    return {"videos": videos[:20]}


@router.get("/video/{path:path}")
async def serve_gallery_video(path: str):
    """Serve a video file from the gallery."""
    file_path = validate_content_path(path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@router.get("/download-all/{influencer}")
async def download_all_gallery_files(influencer: str, source: str = "all"):
    """Download all images and videos for an influencer as a ZIP file."""
    influencer_key = influencer.replace("@", "").lower().replace(" ", "_")
    
    files_to_zip = []
    
    folders = {
        "research": Path("content/seedream4_output"),
        "venice": Path("content/venice_output"),
        "generated": Path(f"content/generated/{influencer_key}"),
        "raw": Path(f"content/raw/{influencer_key}"),
        "final": Path(f"content/final/{influencer_key}"),
        "loops": Path("content/loops"),
    }
    
    valid_extensions = {".png", ".jpg", ".jpeg", ".mp4", ".webm"}
    
    if source == "all":
        for folder_name, folder_path in folders.items():
            if folder_path.exists():
                for file in folder_path.iterdir():
                    if file.suffix.lower() in valid_extensions:
                        files_to_zip.append((file, folder_name))
    else:
        folder_path = folders.get(source)
        if folder_path and folder_path.exists():
            for file in folder_path.iterdir():
                if file.suffix.lower() in valid_extensions:
                    files_to_zip.append((file, source))
    
    if not files_to_zip:
        raise HTTPException(status_code=404, detail="No files found to download")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{influencer_key}_content_{timestamp}.zip"
    
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    
    with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path, folder_name in files_to_zip:
            arcname = f"{folder_name}/{file_path.name}"
            zf.write(file_path, arcname)
    
    return FileResponse(
        temp_zip.name,
        media_type="application/zip",
        filename=zip_filename,
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )
