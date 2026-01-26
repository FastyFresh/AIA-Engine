"""
ManualQueueAgent - Manages the manual posting queue for Instagram and TikTok

Creates and manages a queue of posts that require manual posting
due to platform TOS restrictions on automation.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

from app.pipeline_config import pipeline_settings
from app.agents.packaging_agent import PostPackage

logger = logging.getLogger(__name__)


class ManualQueueItem(BaseModel):
    """A single item in the manual posting queue"""
    item_id: str
    platform: str
    influencer_name: str
    influencer_handle: str
    image_path: str
    caption: str
    suggested_time: str
    created_at: str
    status: str = "pending"
    posted_at: Optional[str] = None
    notes: Optional[str] = None


class ManualQueueAgent:
    """
    Manages manual posting queue for IG and TikTok.
    
    Since Instagram and TikTok don't allow automated posting,
    this agent maintains a queue that appears in the dashboard
    for manual posting from mobile devices.
    """
    
    def __init__(self):
        self.queue_path = Path(pipeline_settings.MANUAL_QUEUE_PATH)
        self.queue_path.mkdir(parents=True, exist_ok=True)
        logger.info("ManualQueueAgent initialized")
    
    async def add_to_queue(
        self,
        package: PostPackage
    ) -> ManualQueueItem:
        """
        Add a post package to the manual queue.
        
        Args:
            package: Post package to add to queue
        """
        item = ManualQueueItem(
            item_id=f"manual_{package.package_id}",
            platform=package.platform,
            influencer_name=package.influencer_name,
            influencer_handle=package.influencer_handle,
            image_path=package.image_path,
            caption=package.caption,
            suggested_time=package.scheduled_time,
            created_at=datetime.now().isoformat(),
            status="pending"
        )
        
        await self._save_item(item)
        
        logger.info(f"Added to manual queue: {item.item_id} for {item.platform}")
        
        return item
    
    async def add_batch_to_queue(
        self,
        packages: List[PostPackage]
    ) -> List[ManualQueueItem]:
        """Add multiple packages to the manual queue"""
        items = []
        
        for package in packages:
            if package.platform in ["instagram_manual", "tiktok_manual"]:
                item = await self.add_to_queue(package)
                items.append(item)
        
        logger.info(f"Added {len(items)} items to manual queue")
        
        return items
    
    async def get_queue(
        self,
        platform: str = None,
        influencer_handle: str = None,
        status: str = None
    ) -> List[ManualQueueItem]:
        """
        Get items from the manual queue.
        
        Args:
            platform: Filter by platform (instagram_manual, tiktok_manual)
            influencer_handle: Filter by influencer
            status: Filter by status (pending, posted)
        """
        items = []
        
        for file_path in self.queue_path.glob("**/*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    for item_data in data:
                        item = ManualQueueItem(**item_data)
                        if self._matches_filter(item, platform, influencer_handle, status):
                            items.append(item)
                else:
                    item = ManualQueueItem(**data)
                    if self._matches_filter(item, platform, influencer_handle, status):
                        items.append(item)
            except Exception as e:
                logger.error(f"Error loading queue item from {file_path}: {e}")
        
        items.sort(key=lambda x: x.suggested_time)
        
        return items
    
    def _matches_filter(
        self,
        item: ManualQueueItem,
        platform: str = None,
        influencer_handle: str = None,
        status: str = None
    ) -> bool:
        """Check if an item matches the given filters"""
        if platform and item.platform != platform:
            return False
        
        if influencer_handle:
            handle = influencer_handle.replace("@", "").lower()
            item_handle = item.influencer_handle.replace("@", "").lower()
            if handle != item_handle:
                return False
        
        if status and item.status != status:
            return False
        
        return True
    
    async def mark_as_posted(
        self,
        item_id: str,
        notes: str = None
    ) -> Optional[ManualQueueItem]:
        """
        Mark a queue item as posted.
        
        Args:
            item_id: ID of the item to mark
            notes: Optional notes about the post
        """
        for file_path in self.queue_path.glob("**/*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                updated = False
                
                if isinstance(data, list):
                    for item_data in data:
                        if item_data.get("item_id") == item_id:
                            item_data["status"] = "posted"
                            item_data["posted_at"] = datetime.now().isoformat()
                            if notes:
                                item_data["notes"] = notes
                            updated = True
                            
                            with open(file_path, "w") as f:
                                json.dump(data, f, indent=2)
                            
                            logger.info(f"Marked {item_id} as posted")
                            return ManualQueueItem(**item_data)
                else:
                    if data.get("item_id") == item_id:
                        data["status"] = "posted"
                        data["posted_at"] = datetime.now().isoformat()
                        if notes:
                            data["notes"] = notes
                        
                        with open(file_path, "w") as f:
                            json.dump(data, f, indent=2)
                        
                        logger.info(f"Marked {item_id} as posted")
                        return ManualQueueItem(**data)
                
            except Exception as e:
                logger.error(f"Error updating queue item in {file_path}: {e}")
        
        logger.warning(f"Queue item not found: {item_id}")
        return None
    
    async def get_queue_stats(
        self,
        influencer_handle: str = None
    ) -> Dict[str, Any]:
        """Get queue statistics"""
        all_items = await self.get_queue(influencer_handle=influencer_handle)
        
        pending_ig = len([i for i in all_items if i.platform == "instagram_manual" and i.status == "pending"])
        pending_tiktok = len([i for i in all_items if i.platform == "tiktok_manual" and i.status == "pending"])
        posted_ig = len([i for i in all_items if i.platform == "instagram_manual" and i.status == "posted"])
        posted_tiktok = len([i for i in all_items if i.platform == "tiktok_manual" and i.status == "posted"])
        
        return {
            "total": len(all_items),
            "pending": {
                "instagram": pending_ig,
                "tiktok": pending_tiktok,
                "total": pending_ig + pending_tiktok
            },
            "posted": {
                "instagram": posted_ig,
                "tiktok": posted_tiktok,
                "total": posted_ig + posted_tiktok
            }
        }
    
    async def _save_item(self, item: ManualQueueItem):
        """Save a queue item to disk"""
        handle = item.influencer_handle.replace("@", "").lower()
        platform = item.platform.replace("_manual", "")
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        item_dir = self.queue_path / handle / platform
        item_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = item_dir / f"{date_str}.json"
        
        existing = []
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    existing = json.load(f)
                if not isinstance(existing, list):
                    existing = [existing]
            except:
                existing = []
        
        existing.append(item.model_dump())
        
        with open(file_path, "w") as f:
            json.dump(existing, f, indent=2)
    
    async def clear_posted(self, days_old: int = 7) -> int:
        """Clear posted items older than specified days"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days_old)
        removed = 0
        
        for file_path in self.queue_path.glob("**/*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    original_len = len(data)
                    data = [
                        item for item in data
                        if not (
                            item.get("status") == "posted" and
                            datetime.fromisoformat(item.get("posted_at", "2099-01-01")) < cutoff
                        )
                    ]
                    removed += original_len - len(data)
                    
                    if data:
                        with open(file_path, "w") as f:
                            json.dump(data, f, indent=2)
                    else:
                        file_path.unlink()
            except Exception as e:
                logger.error(f"Error clearing old items from {file_path}: {e}")
        
        logger.info(f"Cleared {removed} old posted items")
        return removed
