"""
PackagingAgent - Creates structured post packages for distribution

Combines approved images with captions and scheduling to create
ready-to-post packages for each platform.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel

from app.config import INFLUENCERS, InfluencerConfig
from app.pipeline_config import (
    get_pipeline_config,
    pipeline_settings,
    DEFAULT_SUBREDDITS
)
from app.agents.caption_agent import CaptionAgent

logger = logging.getLogger(__name__)


class PostPackage(BaseModel):
    """A ready-to-post content package"""
    package_id: str
    platform: str
    influencer_name: str
    influencer_handle: str
    image_path: str
    caption: str
    title: str = ""
    subreddit: str = ""
    scheduled_time: str
    created_at: str
    status: str = "pending"
    posted_at: Optional[str] = None
    post_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


class PackagingAgent:
    """
    Creates post packages from approved content.
    
    Responsibilities:
    - Read approved images from content/final/
    - Generate platform-specific captions
    - Create structured packages with scheduling
    - Store packages for distribution agents
    """
    
    def __init__(self):
        self.caption_agent = CaptionAgent()
        self.packages_path = Path(pipeline_settings.POST_PACKAGES_PATH)
        self.packages_path.mkdir(parents=True, exist_ok=True)
        logger.info("PackagingAgent initialized")
    
    async def create_packages(
        self,
        influencer: InfluencerConfig,
        tasks: List[Dict[str, Any]],
        approved_images: List[str]
    ) -> Dict[str, Any]:
        """
        Create post packages from approved images and tasks.
        
        Args:
            influencer: Influencer configuration
            tasks: List of generation tasks with platform/style info
            approved_images: List of approved image paths
        """
        handle = influencer.handle.replace("@", "").lower()
        config = get_pipeline_config(handle)
        
        packages = {
            "reddit": [],
            "twitter": [],
            "instagram_manual": [],
            "tiktok_manual": []
        }
        
        reddit_tasks = [t for t in tasks if t.get("platform") == "reddit"]
        twitter_tasks = [t for t in tasks if t.get("platform") == "twitter"]
        ig_tasks = [t for t in tasks if t.get("platform") == "instagram_manual"]
        tiktok_tasks = [t for t in tasks if t.get("platform") == "tiktok_manual"]
        
        image_idx = 0
        
        for task in reddit_tasks:
            if image_idx >= len(approved_images):
                break
            
            image_path = approved_images[image_idx]
            image_idx += 1
            
            metadata = {
                "pose": task.get("pose", ""),
                "outfit_color": task.get("outfit", "").split()[0] if task.get("outfit") else "",
                "mood": task.get("mood", ""),
                "background": task.get("background", "")
            }
            
            package = PostPackage(
                package_id=f"pkg_reddit_{handle}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{image_idx}",
                platform="reddit",
                influencer_name=influencer.name,
                influencer_handle=influencer.handle,
                image_path=image_path,
                caption="",
                title=self.caption_agent.generate_reddit_title(metadata, task.get("subreddit", "")),
                subreddit=task.get("subreddit", "selfie"),
                scheduled_time=task.get("scheduled_time", datetime.now().isoformat()),
                created_at=datetime.now().isoformat(),
                metadata=metadata
            )
            packages["reddit"].append(package)
        
        for task in twitter_tasks:
            if image_idx >= len(approved_images):
                break
            
            image_path = approved_images[image_idx]
            image_idx += 1
            
            metadata = {
                "mood": task.get("mood", ""),
                "pose": task.get("pose", "")
            }
            
            package = PostPackage(
                package_id=f"pkg_twitter_{handle}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{image_idx}",
                platform="twitter",
                influencer_name=influencer.name,
                influencer_handle=influencer.handle,
                image_path=image_path,
                caption=self.caption_agent.generate_twitter_text(metadata),
                scheduled_time=task.get("scheduled_time", datetime.now().isoformat()),
                created_at=datetime.now().isoformat(),
                metadata=metadata
            )
            packages["twitter"].append(package)
        
        for task in ig_tasks:
            if image_idx >= len(approved_images):
                break
            
            image_path = approved_images[image_idx]
            image_idx += 1
            
            metadata = {
                "mood": task.get("mood", ""),
                "pose": task.get("pose", "")
            }
            
            package = PostPackage(
                package_id=f"pkg_ig_{handle}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{image_idx}",
                platform="instagram_manual",
                influencer_name=influencer.name,
                influencer_handle=influencer.handle,
                image_path=image_path,
                caption=self.caption_agent.generate_caption("instagram", metadata),
                scheduled_time=task.get("scheduled_time", datetime.now().isoformat()),
                created_at=datetime.now().isoformat(),
                metadata=metadata
            )
            packages["instagram_manual"].append(package)
        
        for task in tiktok_tasks:
            if image_idx >= len(approved_images):
                break
            
            image_path = approved_images[image_idx]
            image_idx += 1
            
            metadata = {
                "mood": task.get("mood", ""),
                "scenario": f"trying on {task.get('outfit', 'something new')}"
            }
            
            package = PostPackage(
                package_id=f"pkg_tiktok_{handle}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{image_idx}",
                platform="tiktok_manual",
                influencer_name=influencer.name,
                influencer_handle=influencer.handle,
                image_path=image_path,
                caption=self.caption_agent.generate_caption("tiktok", metadata),
                scheduled_time=task.get("scheduled_time", datetime.now().isoformat()),
                created_at=datetime.now().isoformat(),
                metadata=metadata
            )
            packages["tiktok_manual"].append(package)
        
        await self._save_packages(handle, packages)
        
        summary = {
            "influencer": influencer.name,
            "total_packages": sum(len(v) for v in packages.values()),
            "by_platform": {k: len(v) for k, v in packages.items()},
            "packages": {k: [p.model_dump() for p in v] for k, v in packages.items()}
        }
        
        logger.info(f"Created {summary['total_packages']} packages for {influencer.name}")
        
        return summary
    
    async def _save_packages(
        self,
        handle: str,
        packages: Dict[str, List[PostPackage]]
    ):
        """Save packages to disk for distribution agents"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        for platform, platform_packages in packages.items():
            if not platform_packages:
                continue
            
            platform_dir = self.packages_path / handle / platform
            platform_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = platform_dir / f"{date_str}.json"
            
            existing = []
            if file_path.exists():
                try:
                    with open(file_path, "r") as f:
                        existing = json.load(f)
                except:
                    existing = []
            
            all_packages = existing + [p.model_dump() for p in platform_packages]
            
            with open(file_path, "w") as f:
                json.dump(all_packages, f, indent=2)
            
            logger.info(f"Saved {len(platform_packages)} packages to {file_path}")
    
    async def get_pending_packages(
        self,
        influencer_handle: str,
        platform: str = None
    ) -> List[PostPackage]:
        """Get pending packages for posting"""
        handle = influencer_handle.replace("@", "").lower()
        packages = []
        
        platforms = [platform] if platform else ["reddit", "twitter", "instagram_manual", "tiktok_manual"]
        
        for plat in platforms:
            platform_dir = self.packages_path / handle / plat
            if not platform_dir.exists():
                continue
            
            for file_path in platform_dir.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                    
                    for pkg_data in data:
                        if pkg_data.get("status") == "pending":
                            packages.append(PostPackage(**pkg_data))
                except Exception as e:
                    logger.error(f"Error loading packages from {file_path}: {e}")
        
        return packages
    
    async def mark_package_posted(
        self,
        package_id: str,
        post_url: str = None
    ) -> bool:
        """Mark a package as posted"""
        for handle_dir in self.packages_path.iterdir():
            if not handle_dir.is_dir():
                continue
            
            for platform_dir in handle_dir.iterdir():
                if not platform_dir.is_dir():
                    continue
                
                for file_path in platform_dir.glob("*.json"):
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)
                        
                        updated = False
                        for pkg in data:
                            if pkg.get("package_id") == package_id:
                                pkg["status"] = "posted"
                                pkg["posted_at"] = datetime.now().isoformat()
                                if post_url:
                                    pkg["post_url"] = post_url
                                updated = True
                                break
                        
                        if updated:
                            with open(file_path, "w") as f:
                                json.dump(data, f, indent=2)
                            logger.info(f"Marked package {package_id} as posted")
                            return True
                    except Exception as e:
                        logger.error(f"Error updating package in {file_path}: {e}")
        
        return False
