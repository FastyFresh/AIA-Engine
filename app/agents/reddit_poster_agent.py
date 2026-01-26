"""
RedditPosterAgent - Automated Reddit posting via PRAW

Posts approved content to specified subreddits using the Reddit API.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from app.pipeline_config import pipeline_settings
from app.agents.packaging_agent import PostPackage

logger = logging.getLogger(__name__)

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logger.warning("PRAW not installed. Reddit posting will be disabled.")


class RedditPosterAgent:
    """
    Posts content to Reddit using PRAW.
    
    Requires environment variables:
    - REDDIT_CLIENT_ID
    - REDDIT_CLIENT_SECRET
    - REDDIT_USERNAME
    - REDDIT_PASSWORD
    - REDDIT_USER_AGENT
    """
    
    def __init__(self):
        self.reddit = None
        self._initialize_reddit()
        logger.info("RedditPosterAgent initialized")
    
    def _initialize_reddit(self):
        """Initialize Reddit client if credentials are available"""
        if not PRAW_AVAILABLE:
            logger.warning("PRAW not available, Reddit posting disabled")
            return
        
        client_id = pipeline_settings.REDDIT_CLIENT_ID
        client_secret = pipeline_settings.REDDIT_CLIENT_SECRET
        username = pipeline_settings.REDDIT_USERNAME
        password = pipeline_settings.REDDIT_PASSWORD
        user_agent = pipeline_settings.REDDIT_USER_AGENT
        
        if not all([client_id, client_secret, username, password]):
            logger.warning("Reddit credentials not configured")
            return
        
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                username=username,
                password=password,
                user_agent=user_agent
            )
            logger.info(f"Reddit client initialized for user: {username}")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            self.reddit = None
    
    async def post(
        self,
        package: PostPackage,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Post a package to Reddit.
        
        Args:
            package: Post package with image, title, and subreddit
            dry_run: If True, log without posting
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would post to r/{package.subreddit}: {package.title}")
            return {
                "status": "dry_run",
                "package_id": package.package_id,
                "subreddit": package.subreddit,
                "title": package.title,
                "message": "Dry run - no actual post made"
            }
        
        if not self.reddit:
            return {
                "status": "error",
                "package_id": package.package_id,
                "error": "Reddit client not initialized. Check credentials."
            }
        
        try:
            subreddit = self.reddit.subreddit(package.subreddit)
            
            image_path = Path(package.image_path)
            if not image_path.exists():
                return {
                    "status": "error",
                    "package_id": package.package_id,
                    "error": f"Image not found: {package.image_path}"
                }
            
            submission = subreddit.submit_image(
                title=package.title,
                image_path=str(image_path),
                nsfw=False
            )
            
            logger.info(f"Posted to r/{package.subreddit}: {submission.url}")
            
            return {
                "status": "success",
                "package_id": package.package_id,
                "subreddit": package.subreddit,
                "title": package.title,
                "post_url": f"https://reddit.com{submission.permalink}",
                "submission_id": submission.id,
                "posted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to post to Reddit: {e}")
            return {
                "status": "error",
                "package_id": package.package_id,
                "subreddit": package.subreddit,
                "error": str(e)
            }
    
    async def post_batch(
        self,
        packages: List[PostPackage],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Post multiple packages to Reddit"""
        results = {
            "successful": [],
            "failed": [],
            "dry_run": dry_run
        }
        
        for package in packages:
            result = await self.post(package, dry_run=dry_run)
            
            if result.get("status") == "success" or result.get("status") == "dry_run":
                results["successful"].append(result)
            else:
                results["failed"].append(result)
        
        summary = {
            "total": len(packages),
            "successful": len(results["successful"]),
            "failed": len(results["failed"]),
            "dry_run": dry_run,
            "results": results
        }
        
        logger.info(f"Reddit batch complete: {summary['successful']}/{summary['total']} successful")
        
        return summary
    
    def is_configured(self) -> bool:
        """Check if Reddit client is properly configured"""
        return self.reddit is not None
    
    def get_karma(self) -> Dict[str, int]:
        """Get current account karma"""
        if not self.reddit:
            return {"error": "Not configured"}
        
        try:
            me = self.reddit.user.me()
            return {
                "link_karma": me.link_karma,
                "comment_karma": me.comment_karma,
                "total_karma": me.link_karma + me.comment_karma
            }
        except Exception as e:
            return {"error": str(e)}
