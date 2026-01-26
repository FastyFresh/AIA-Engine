"""
Object Storage API Routes

Provides endpoints for file uploads and downloads using Replit Object Storage.
"""

import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.object_storage import object_storage_service, ObjectNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/storage", tags=["Object Storage"])

uploads_router = APIRouter(prefix="/api/uploads", tags=["Uploads"])


class UploadUrlRequest(BaseModel):
    """Request body for getting an upload URL."""
    name: str
    size: Optional[int] = None
    content_type: Optional[str] = None


class UploadUrlResponse(BaseModel):
    """Response containing the presigned upload URL."""
    upload_url: str
    object_path: str
    object_id: str


@router.get("/status")
async def storage_status():
    """Check object storage configuration status."""
    return {
        "configured": object_storage_service.is_configured,
        "bucket_id": object_storage_service.bucket_id or None,
        "has_public_paths": bool(object_storage_service.get_public_paths()),
        "has_private_dir": bool(object_storage_service.get_private_dir()),
    }


@router.post("/request-upload-url", response_model=UploadUrlResponse)
async def request_upload_url(request: UploadUrlRequest):
    """
    Get a presigned URL for uploading a file.
    
    This implements the two-step upload flow:
    1. Client calls this endpoint with file metadata (name, size, type)
    2. Client uploads file directly to the returned presigned URL
    
    The file is uploaded directly to Google Cloud Storage, not to this server.
    """
    if not object_storage_service.is_configured:
        raise HTTPException(status_code=503, detail="Object storage not configured")
    
    try:
        content_type = request.content_type or "application/octet-stream"
        result = await object_storage_service.get_upload_url(
            filename=request.name,
            content_type=content_type,
            prefix="uploads",
        )
        
        return UploadUrlResponse(
            upload_url=result["upload_url"],
            object_path=result["object_path"],
            object_id=result["object_id"],
        )
    except Exception as e:
        logger.error(f"Failed to generate upload URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@uploads_router.post("/request-url", response_model=UploadUrlResponse)
async def request_upload_url_alias(request: UploadUrlRequest):
    """
    Alias for /api/storage/request-upload-url to match client expectations.
    """
    return await request_upload_url(request)


@router.post("/upload-content-image")
async def upload_content_image(
    file: UploadFile = File(...),
    influencer: str = "starbright_monroe",
    category: str = "generated",
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Upload a content image directly (server-side upload).
    
    This is for internal/admin use when the server generates content.
    Requires X-Admin-Key header for authentication.
    For client uploads, use the presigned URL flow instead.
    """
    import os
    admin_key = os.environ.get("ADMIN_API_KEY", "")
    if not admin_key or x_admin_key != admin_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not object_storage_service.is_configured:
        raise HTTPException(status_code=503, detail="Object storage not configured")
    
    try:
        import tempfile
        import shutil
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or "image.png").suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = Path(tmp.name)
        
        try:
            object_name = f"content/{influencer}/{category}/{file.filename}"
            object_path = await object_storage_service.upload_file(
                file_path=tmp_path,
                object_name=object_name,
                content_type=file.content_type,
                public=True,
            )
            
            return {
                "success": True,
                "object_path": object_path,
                "filename": file.filename,
            }
        finally:
            tmp_path.unlink(missing_ok=True)
            
    except Exception as e:
        logger.error(f"Failed to upload content image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public-url/{path:path}")
async def get_public_url(path: str, ttl: int = 3600):
    """
    Get a signed URL for accessing a public object.
    
    Args:
        path: The object path (e.g., "content/starbright/image.png")
        ttl: URL validity in seconds (default 1 hour)
    """
    if not object_storage_service.is_configured:
        raise HTTPException(status_code=503, detail="Object storage not configured")
    
    try:
        url = await object_storage_service.get_public_url(path, ttl_seconds=ttl)
        return {"url": url, "expires_in": ttl}
    except ObjectNotFoundError:
        raise HTTPException(status_code=404, detail="Object not found")
    except Exception as e:
        logger.error(f"Failed to get public URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))
