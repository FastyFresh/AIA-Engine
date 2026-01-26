"""
Python Object Storage Service for Replit

Uses the Replit sidecar endpoint for authentication and signed URL generation.
"""

import os
import json
import logging
import httpx
from pathlib import Path
from typing import Optional, Dict, Any, List
from uuid import uuid4

logger = logging.getLogger(__name__)

REPLIT_SIDECAR_ENDPOINT = "http://127.0.0.1:1106"


class ObjectNotFoundError(Exception):
    """Raised when an object is not found in storage."""
    pass


class ObjectStorageService:
    """
    Service for interacting with Replit Object Storage.
    
    Provides methods for:
    - Generating presigned upload URLs
    - Uploading files directly
    - Downloading files
    - Listing objects
    """
    
    def __init__(self):
        self.bucket_id = os.environ.get("DEFAULT_OBJECT_STORAGE_BUCKET_ID", "")
        self.public_paths = os.environ.get("PUBLIC_OBJECT_SEARCH_PATHS", "")
        self.private_dir = os.environ.get("PRIVATE_OBJECT_DIR", "")
        
        if self.bucket_id:
            logger.info(f"ObjectStorageService initialized with bucket: {self.bucket_id}")
        else:
            logger.warning("Object storage not configured - DEFAULT_OBJECT_STORAGE_BUCKET_ID not set")
    
    @property
    def is_configured(self) -> bool:
        """Check if object storage is properly configured."""
        return bool(self.bucket_id)
    
    def get_public_paths(self) -> List[str]:
        """Get the list of public object search paths."""
        if not self.public_paths:
            return []
        return [p.strip() for p in self.public_paths.split(",") if p.strip()]
    
    def get_private_dir(self) -> str:
        """Get the private object directory."""
        return self.private_dir
    
    async def get_signed_url(
        self,
        object_name: str,
        method: str = "GET",
        ttl_seconds: int = 3600,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Get a signed URL for an object.
        
        Args:
            object_name: The name/path of the object within the bucket
            method: HTTP method (GET, PUT, DELETE, HEAD)
            ttl_seconds: Time-to-live for the signed URL in seconds
            content_type: Content type for uploads
            
        Returns:
            Signed URL string
        """
        if not self.bucket_id:
            raise ValueError("Object storage not configured")
        
        from datetime import datetime, timedelta, timezone
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
        
        request_body = {
            "bucket_name": self.bucket_id,
            "object_name": object_name,
            "method": method,
            "expires_at": expires_at,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{REPLIT_SIDECAR_ENDPOINT}/object-storage/signed-object-url",
                json=request_body,
                timeout=30.0,
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get signed URL: {response.status_code} - {response.text}")
            
            data = response.json()
            return data["signed_url"]
    
    async def get_upload_url(
        self,
        filename: str,
        content_type: str = "application/octet-stream",
        prefix: str = "uploads",
    ) -> Dict[str, str]:
        """
        Get a presigned URL for uploading a file.
        
        Args:
            filename: Original filename
            content_type: MIME type of the file
            prefix: Path prefix within the private directory
            
        Returns:
            Dict with 'upload_url', 'object_path', and 'object_id'
        """
        object_id = str(uuid4())
        
        private_dir = self.get_private_dir()
        if not private_dir:
            private_dir = f"/{self.bucket_id}/.private"
        
        if private_dir.startswith("/"):
            private_dir = private_dir[1:]
        
        parts = private_dir.split("/", 1)
        actual_object_path = parts[1] if len(parts) > 1 else ".private"
        
        full_object_name = f"{actual_object_path}/{prefix}/{object_id}/{filename}".replace("//", "/")
        
        signed_url = await self.get_signed_url(
            object_name=full_object_name,
            method="PUT",
            ttl_seconds=900,
            content_type=content_type,
        )
        
        return {
            "upload_url": signed_url,
            "object_path": f"/{self.bucket_id}/{full_object_name}",
            "object_id": object_id,
        }
    
    async def upload_file(
        self,
        file_path: Path,
        object_name: str,
        content_type: Optional[str] = None,
        public: bool = False,
    ) -> str:
        """
        Upload a local file to object storage.
        
        Args:
            file_path: Local path to the file
            object_name: Name/path for the object in storage
            content_type: MIME type (auto-detected if not provided)
            public: Whether to store in public or private directory
            
        Returns:
            The object path in storage
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if content_type is None:
            import mimetypes
            content_type, _ = mimetypes.guess_type(str(file_path))
            content_type = content_type or "application/octet-stream"
        
        if public:
            paths = self.get_public_paths()
            if not paths:
                raise ValueError("No public paths configured")
            base_path = paths[0]
        else:
            base_path = self.get_private_dir()
            if not base_path:
                base_path = f"/{self.bucket_id}/.private"
        
        full_path = f"{base_path}/{object_name}".replace("//", "/")
        if full_path.startswith("/"):
            full_path = full_path[1:]
        
        parts = full_path.split("/", 1)
        object_path = parts[1] if len(parts) > 1 else object_name
        
        signed_url = await self.get_signed_url(
            object_name=object_path,
            method="PUT",
            ttl_seconds=900,
            content_type=content_type,
        )
        
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            response = await client.put(
                signed_url,
                content=file_content,
                headers={"Content-Type": content_type},
                timeout=300.0,
            )
            
            if response.status_code not in (200, 201):
                raise Exception(f"Failed to upload: {response.status_code} - {response.text}")
        
        logger.info(f"Uploaded {file_path} to {full_path}")
        return full_path
    
    async def download_file(
        self,
        object_name: str,
        destination: Path,
        public: bool = False,
    ) -> Path:
        """
        Download a file from object storage.
        
        Args:
            object_name: Name/path of the object in storage
            destination: Local path to save the file
            public: Whether the object is in public or private directory
            
        Returns:
            Path to the downloaded file
        """
        if public:
            paths = self.get_public_paths()
            if not paths:
                raise ValueError("No public paths configured")
            base_path = paths[0]
        else:
            base_path = self.get_private_dir()
        
        full_path = f"{base_path}/{object_name}".replace("//", "/")
        if full_path.startswith("/"):
            full_path = full_path[1:]
        
        parts = full_path.split("/", 1)
        object_path = parts[1] if len(parts) > 1 else object_name
        
        signed_url = await self.get_signed_url(
            object_name=object_path,
            method="GET",
            ttl_seconds=3600,
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.get(signed_url, timeout=300.0)
            
            if response.status_code == 404:
                raise ObjectNotFoundError(f"Object not found: {object_name}")
            
            if response.status_code != 200:
                raise Exception(f"Failed to download: {response.status_code}")
        
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        
        logger.info(f"Downloaded {object_name} to {destination}")
        return destination
    
    async def get_public_url(self, object_name: str, ttl_seconds: int = 3600) -> str:
        """
        Get a signed URL for reading a public object.
        
        Args:
            object_name: Name/path of the object
            ttl_seconds: How long the URL should be valid
            
        Returns:
            Signed URL for accessing the object
        """
        paths = self.get_public_paths()
        if not paths:
            raise ValueError("No public paths configured")
        
        base_path = paths[0]
        full_path = f"{base_path}/{object_name}".replace("//", "/")
        if full_path.startswith("/"):
            full_path = full_path[1:]
        
        parts = full_path.split("/", 1)
        object_path = parts[1] if len(parts) > 1 else object_name
        
        return await self.get_signed_url(
            object_name=object_path,
            method="GET",
            ttl_seconds=ttl_seconds,
        )
    
    async def list_objects(self, prefix: str = "", public: bool = True) -> List[Dict[str, Any]]:
        """
        List objects with a given prefix.
        
        Note: This is a simplified implementation. For full listing,
        use the GCS client directly.
        
        Args:
            prefix: Path prefix to filter objects
            public: Whether to list from public or private directory
            
        Returns:
            List of object metadata dicts
        """
        logger.warning("list_objects not fully implemented - returning empty list")
        return []


object_storage_service = ObjectStorageService()
