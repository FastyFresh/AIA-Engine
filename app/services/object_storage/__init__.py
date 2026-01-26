"""
Replit Object Storage Service for Python/FastAPI

This module provides a Python implementation of Replit's object storage,
using the sidecar endpoint for signed URL generation.
"""

from .object_storage_service import (
    ObjectStorageService,
    ObjectNotFoundError,
    object_storage_service,
)

__all__ = [
    "ObjectStorageService",
    "ObjectNotFoundError", 
    "object_storage_service",
]
