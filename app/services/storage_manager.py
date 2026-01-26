"""
Storage Manager - Disk space management and cleanup utilities.

Provides tools for monitoring disk usage, ensuring sufficient space for writes,
and cleaning up temporary files.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger(__name__)

CLEANUP_DIRS = [
    "tmp",
    "cache", 
    "outputs",
    "artifacts",
    "logs",
]

CONTENT_DIR = Path("content")
FINAL_DIR = CONTENT_DIR / "final"
RAW_DIR = CONTENT_DIR / "raw"


class StorageManager:
    """Manages local disk storage, cleanup, and space verification."""
    
    def __init__(self):
        self.workspace_path = Path(os.environ.get("HOME", "/home/runner")) / "workspace"
        self.min_free_mb = float(os.environ.get("MIN_FREE_DISK_MB", "500"))
        
    def get_disk_usage(self) -> Dict[str, Any]:
        """Get current disk usage statistics."""
        try:
            total, used, free = shutil.disk_usage(self.workspace_path)
            return {
                "total_mb": round(total / (1024 * 1024), 2),
                "used_mb": round(used / (1024 * 1024), 2),
                "free_mb": round(free / (1024 * 1024), 2),
                "percent_used": round((used / total) * 100, 2),
            }
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            return {
                "total_mb": 0,
                "used_mb": 0,
                "free_mb": 0,
                "percent_used": 0,
                "error": str(e),
            }
    
    def check_disk_space(self, required_mb: float = 100.0) -> Tuple[bool, str]:
        """
        Check if there's enough disk space available.
        
        Args:
            required_mb: Minimum required free space in MB
            
        Returns:
            Tuple of (has_space, message)
        """
        usage = self.get_disk_usage()
        free_mb = usage.get("free_mb", 0)
        
        if free_mb >= required_mb:
            return True, f"Sufficient space available: {free_mb:.2f}MB free"
        else:
            return False, f"Insufficient space: {free_mb:.2f}MB free, {required_mb:.2f}MB required"
    
    def ensure_space_for_write(self, estimated_size_mb: float = 5.0) -> bool:
        """
        Ensure there's enough space for a write operation.
        
        Args:
            estimated_size_mb: Estimated size of the write in MB
            
        Returns:
            True if space is available, False otherwise
        """
        required = estimated_size_mb + self.min_free_mb
        has_space, message = self.check_disk_space(required)
        
        if not has_space:
            logger.warning(f"Low disk space: {message}")
            self.run_cleanup(dry_run=False)
            has_space, message = self.check_disk_space(required)
            
        return has_space
    
    def get_dir_size(self, path: Path) -> int:
        """Get total size of a directory in bytes."""
        total = 0
        try:
            if path.exists() and path.is_dir():
                for entry in path.rglob("*"):
                    if entry.is_file():
                        total += entry.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating size of {path}: {e}")
        return total
    
    def get_storage_report(self) -> Dict[str, Any]:
        """Generate a storage usage report."""
        report = {
            "disk_usage": self.get_disk_usage(),
            "directories": {},
        }
        
        for dir_name in CLEANUP_DIRS + ["content"]:
            dir_path = self.workspace_path / dir_name
            if dir_path.exists():
                size_bytes = self.get_dir_size(dir_path)
                report["directories"][dir_name] = {
                    "size_mb": round(size_bytes / (1024 * 1024), 2),
                    "path": str(dir_path),
                }
        
        return report
    
    def run_cleanup(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up temporary directories to free disk space.
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Report of cleanup actions
        """
        result = {
            "dry_run": dry_run,
            "cleaned": [],
            "errors": [],
            "space_freed_mb": 0,
        }
        
        for dir_name in CLEANUP_DIRS:
            dir_path = self.workspace_path / dir_name
            if not dir_path.exists():
                continue
                
            try:
                size_before = self.get_dir_size(dir_path)
                size_mb = round(size_before / (1024 * 1024), 2)
                
                if size_mb > 0:
                    if dry_run:
                        result["cleaned"].append({
                            "directory": dir_name,
                            "would_free_mb": size_mb,
                        })
                    else:
                        for item in dir_path.iterdir():
                            try:
                                if item.is_file():
                                    item.unlink()
                                elif item.is_dir():
                                    shutil.rmtree(item)
                            except Exception as e:
                                result["errors"].append(f"Failed to delete {item}: {e}")
                        
                        result["cleaned"].append({
                            "directory": dir_name,
                            "freed_mb": size_mb,
                        })
                        result["space_freed_mb"] += size_mb
                        
            except Exception as e:
                result["errors"].append(f"Error cleaning {dir_name}: {e}")
        
        return result
    
    async def approve_with_offload(
        self,
        source_path: Path,
        final_dir: Path,
        delete_source: bool = False,
        offload_to_cloud: bool = True,
    ) -> Dict[str, Any]:
        """
        Approve content by moving to final directory and optionally offload to cloud storage.
        
        Args:
            source_path: Path to the source image file
            final_dir: Directory to move approved content to
            delete_source: Whether to delete the source after copying
            offload_to_cloud: Whether to upload to object storage
            
        Returns:
            Result of the approval operation
        """
        result = {
            "status": "success",
            "source_path": str(source_path),
            "final_path": None,
            "offloaded": False,
            "cleanup_performed": False,
        }
        
        try:
            source = Path(source_path) if isinstance(source_path, str) else source_path
            
            if not source.exists():
                result["status"] = "error"
                result["error"] = f"Source file not found: {source}"
                return result
            
            if not self.ensure_space_for_write(estimated_size_mb=5.0):
                result["cleanup_performed"] = True
                if not self.ensure_space_for_write(estimated_size_mb=5.0):
                    result["status"] = "error"
                    result["error"] = "Insufficient disk space even after cleanup"
                    return result
            
            final_dir.mkdir(parents=True, exist_ok=True)
            final_path = final_dir / source.name
            
            if delete_source:
                shutil.move(str(source), str(final_path))
            else:
                shutil.copy2(str(source), str(final_path))
            
            result["final_path"] = str(final_path)
            
            if offload_to_cloud:
                try:
                    from app.services.object_storage import object_storage_service
                    
                    if object_storage_service.is_configured:
                        object_name = f"approved/{final_dir.name}/{final_path.name}"
                        await object_storage_service.upload_file(
                            file_path=final_path,
                            object_name=object_name,
                            public=False,
                        )
                        result["offloaded"] = True
                        result["cloud_path"] = object_name
                        logger.info(f"Offloaded {final_path.name} to cloud storage")
                except Exception as e:
                    logger.warning(f"Failed to offload to cloud: {e}")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Approval failed: {e}")
        
        return result


storage_manager = StorageManager()
