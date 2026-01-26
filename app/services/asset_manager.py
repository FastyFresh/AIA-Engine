"""
AssetManager - Post-approval persistence and routing service.

This is a stub implementation for the future asset management pipeline.
When fully implemented, this service will:
- Persist approved images to permanent storage
- Track asset metadata in the database
- Route approved assets to downstream agents (Editing, Publishing)
- Manage asset lifecycle states

See docs/ARCHITECTURE_ROADMAP.md for full interface specification.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import os
import shutil

from app.config import settings

logger = logging.getLogger(__name__)


class AssetStatus(Enum):
    """Lifecycle states for managed assets."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    READY_TO_PUBLISH = "ready_to_publish"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class AssetRecord:
    """Represents a managed content asset."""
    asset_id: str
    influencer: str
    image_path: str
    status: AssetStatus
    created_at: datetime
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    platform: Optional[str] = None
    post_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        if self.approved_at:
            data["approved_at"] = self.approved_at.isoformat()
        if self.published_at:
            data["published_at"] = self.published_at.isoformat()
        return data


class AssetManager:
    """
    Manages the lifecycle of approved content assets.
    
    Future Implementation Notes:
    - Replace in-memory storage with PostgreSQL
    - Add object storage integration (S3/R2) for images
    - Implement event emission for downstream agents
    """
    
    def __init__(self):
        self._assets: Dict[str, AssetRecord] = {}
        self._counter = 0
        self.final_storage_path = getattr(settings, 'CONTENT_FINAL_PATH', 'content/final')
        os.makedirs(self.final_storage_path, exist_ok=True)
        logger.info("AssetManager initialized (stub implementation)")
    
    def _generate_asset_id(self) -> str:
        """Generate a unique asset ID."""
        self._counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"asset_{timestamp}_{self._counter:04d}"
    
    async def save_approved(
        self,
        image_path: str,
        influencer: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AssetRecord:
        """
        Save an approved image to permanent storage and create an asset record.
        
        Args:
            image_path: Path to the approved image
            influencer: Influencer name/handle
            metadata: Additional metadata (prompt, quality score, etc.)
            
        Returns:
            AssetRecord with the asset details
        """
        asset_id = self._generate_asset_id()
        
        influencer_folder = influencer.lower().replace(" ", "_")
        dest_folder = os.path.join(self.final_storage_path, influencer_folder)
        os.makedirs(dest_folder, exist_ok=True)
        
        filename = os.path.basename(image_path)
        dest_path = os.path.join(dest_folder, f"{asset_id}_{filename}")
        
        if os.path.exists(image_path):
            shutil.copy2(image_path, dest_path)
            logger.info(f"Copied approved image to: {dest_path}")
        else:
            dest_path = image_path
            logger.warning(f"Source image not found, keeping original path: {image_path}")
        
        record = AssetRecord(
            asset_id=asset_id,
            influencer=influencer,
            image_path=dest_path,
            status=AssetStatus.APPROVED,
            created_at=datetime.now(),
            approved_at=datetime.now(),
            metadata=metadata
        )
        
        self._assets[asset_id] = record
        logger.info(f"Created asset record: {asset_id} for {influencer}")
        
        return record
    
    async def get_pending_for_publish(
        self,
        influencer: str,
        limit: int = 10
    ) -> List[AssetRecord]:
        """
        Get approved assets ready for publishing.
        
        Args:
            influencer: Filter by influencer name
            limit: Maximum number of assets to return
            
        Returns:
            List of AssetRecords ready for publishing
        """
        ready_statuses = {AssetStatus.APPROVED, AssetStatus.READY_TO_PUBLISH}
        
        matching = [
            asset for asset in self._assets.values()
            if asset.influencer.lower() == influencer.lower()
            and asset.status in ready_statuses
        ]
        
        matching.sort(key=lambda x: x.created_at, reverse=True)
        
        return matching[:limit]
    
    async def mark_published(
        self,
        asset_id: str,
        platform: str,
        post_url: str
    ) -> Optional[AssetRecord]:
        """
        Mark an asset as published.
        
        Args:
            asset_id: The asset ID to update
            platform: Platform where it was published (instagram, tiktok, etc.)
            post_url: URL to the published post
            
        Returns:
            Updated AssetRecord or None if not found
        """
        if asset_id not in self._assets:
            logger.warning(f"Asset not found: {asset_id}")
            return None
        
        record = self._assets[asset_id]
        record.status = AssetStatus.PUBLISHED
        record.published_at = datetime.now()
        record.platform = platform
        record.post_url = post_url
        
        logger.info(f"Marked asset {asset_id} as published on {platform}")
        
        return record
    
    async def get_asset(self, asset_id: str) -> Optional[AssetRecord]:
        """Get an asset by ID."""
        return self._assets.get(asset_id)
    
    async def list_assets(
        self,
        influencer: Optional[str] = None,
        status: Optional[AssetStatus] = None,
        limit: int = 50
    ) -> List[AssetRecord]:
        """List assets with optional filtering."""
        results = list(self._assets.values())
        
        if influencer:
            results = [a for a in results if a.influencer.lower() == influencer.lower()]
        
        if status:
            results = [a for a in results if a.status == status]
        
        results.sort(key=lambda x: x.created_at, reverse=True)
        
        return results[:limit]


asset_manager = AssetManager()
