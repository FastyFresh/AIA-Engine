#!/usr/bin/env python3
"""
Migration script to upload content files to Replit Object Storage.

This script uploads files from the local content/ directory to Object Storage,
maintaining the same directory structure.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
import mimetypes

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.object_storage import object_storage_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CONTENT_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.webm', '.mov'}

PRIORITY_FOLDERS = [
    'content/generated',
    'content/final', 
    'content/loops',
    'content/references',
    'content/telegram',
]

SKIP_FOLDERS = [
    'content/archives',
    'content/omnime_training',
    'content/omnime_training_optimized',
    'content/omnime_training_thin_face',
    'content/prompt_cache',
    'content/research_cache',
]


class MigrationStats:
    def __init__(self):
        self.uploaded = 0
        self.skipped = 0
        self.failed = 0
        self.total_bytes = 0
    
    def __str__(self):
        return f"Uploaded: {self.uploaded}, Skipped: {self.skipped}, Failed: {self.failed}, Total: {self.total_bytes / (1024*1024):.1f}MB"


async def upload_file(file_path: Path, stats: MigrationStats) -> bool:
    """Upload a single file to object storage."""
    try:
        relative_path = str(file_path)
        if relative_path.startswith('content/'):
            object_name = relative_path
        else:
            object_name = f"content/{relative_path}"
        
        content_type, _ = mimetypes.guess_type(str(file_path))
        content_type = content_type or 'application/octet-stream'
        
        await object_storage_service.upload_file(
            file_path=file_path,
            object_name=object_name,
            content_type=content_type,
            public=True,
        )
        
        stats.uploaded += 1
        stats.total_bytes += file_path.stat().st_size
        return True
        
    except Exception as e:
        logger.error(f"Failed to upload {file_path}: {e}")
        stats.failed += 1
        return False


async def migrate_folder(folder_path: Path, stats: MigrationStats, batch_size: int = 10):
    """Migrate all content files in a folder."""
    if not folder_path.exists():
        logger.warning(f"Folder not found: {folder_path}")
        return
    
    files_to_upload = []
    for file_path in folder_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in CONTENT_EXTENSIONS:
            files_to_upload.append(file_path)
    
    logger.info(f"Found {len(files_to_upload)} files to migrate in {folder_path}")
    
    for i in range(0, len(files_to_upload), batch_size):
        batch = files_to_upload[i:i + batch_size]
        tasks = [upload_file(f, stats) for f in batch]
        await asyncio.gather(*tasks)
        
        if (i + batch_size) % 50 == 0:
            logger.info(f"Progress: {i + batch_size}/{len(files_to_upload)} - {stats}")


async def run_migration(folders: Optional[List[str]] = None, dry_run: bool = False):
    """Run the migration for specified folders."""
    if not object_storage_service.is_configured:
        logger.error("Object storage is not configured!")
        return
    
    logger.info(f"Object Storage bucket: {object_storage_service.bucket_id}")
    
    if folders is None:
        folders = PRIORITY_FOLDERS
    
    stats = MigrationStats()
    
    for folder in folders:
        folder_path = Path(folder)
        if any(folder.startswith(skip) for skip in SKIP_FOLDERS):
            logger.info(f"Skipping {folder}")
            continue
        
        logger.info(f"\n=== Migrating {folder} ===")
        
        if dry_run:
            count = sum(1 for f in folder_path.rglob('*') 
                       if f.is_file() and f.suffix.lower() in CONTENT_EXTENSIONS)
            logger.info(f"[DRY RUN] Would upload {count} files from {folder}")
        else:
            await migrate_folder(folder_path, stats)
    
    logger.info(f"\n=== Migration Complete ===")
    logger.info(f"Final stats: {stats}")
    return stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate content to Object Storage')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be uploaded')
    parser.add_argument('--folders', nargs='+', help='Specific folders to migrate')
    parser.add_argument('--all', action='store_true', help='Migrate all content folders')
    
    args = parser.parse_args()
    
    if args.all:
        folders = ['content/']
    elif args.folders:
        folders = args.folders
    else:
        folders = PRIORITY_FOLDERS
    
    asyncio.run(run_migration(folders=folders, dry_run=args.dry_run))
