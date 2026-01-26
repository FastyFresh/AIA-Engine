"""
TwitterPosterAgent - Automated Twitter/X posting via API

Posts approved content to Twitter/X using the API v2.
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
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    logger.warning("Tweepy not installed. Twitter posting will be disabled.")


class TwitterPosterAgent:
    """
    Posts content to Twitter/X using Tweepy.
    
    Requires environment variables:
    - TWITTER_API_KEY
    - TWITTER_API_SECRET
    - TWITTER_ACCESS_TOKEN
    - TWITTER_ACCESS_SECRET
    """
    
    def __init__(self):
        self.client = None
        self.api = None
        self._initialize_twitter()
        logger.info("TwitterPosterAgent initialized")
    
    def _initialize_twitter(self):
        """Initialize Twitter client if credentials are available"""
        if not TWEEPY_AVAILABLE:
            logger.warning("Tweepy not available, Twitter posting disabled")
            return
        
        api_key = pipeline_settings.TWITTER_API_KEY
        api_secret = pipeline_settings.TWITTER_API_SECRET
        access_token = pipeline_settings.TWITTER_ACCESS_TOKEN
        access_secret = pipeline_settings.TWITTER_ACCESS_SECRET
        
        if not all([api_key, api_secret, access_token, access_secret]):
            logger.warning("Twitter credentials not configured")
            return
        
        try:
            auth = tweepy.OAuthHandler(api_key, api_secret)
            auth.set_access_token(access_token, access_secret)
            self.api = tweepy.API(auth)
            
            self.client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret
            )
            
            logger.info("Twitter client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")
            self.client = None
            self.api = None
    
    async def post(
        self,
        package: PostPackage,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Post a package to Twitter.
        
        Args:
            package: Post package with image and caption
            dry_run: If True, log without posting
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would tweet: {package.caption[:50]}...")
            return {
                "status": "dry_run",
                "package_id": package.package_id,
                "text": package.caption,
                "message": "Dry run - no actual tweet made"
            }
        
        if not self.client or not self.api:
            return {
                "status": "error",
                "package_id": package.package_id,
                "error": "Twitter client not initialized. Check credentials."
            }
        
        try:
            image_path = Path(package.image_path)
            if not image_path.exists():
                return {
                    "status": "error",
                    "package_id": package.package_id,
                    "error": f"Image not found: {package.image_path}"
                }
            
            media = self.api.media_upload(str(image_path))
            
            response = self.client.create_tweet(
                text=package.caption,
                media_ids=[media.media_id]
            )
            
            tweet_id = response.data.get("id")
            tweet_url = f"https://twitter.com/i/status/{tweet_id}" if tweet_id else None
            
            logger.info(f"Posted tweet: {tweet_url}")
            
            return {
                "status": "success",
                "package_id": package.package_id,
                "text": package.caption,
                "tweet_id": tweet_id,
                "post_url": tweet_url,
                "posted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to post to Twitter: {e}")
            return {
                "status": "error",
                "package_id": package.package_id,
                "error": str(e)
            }
    
    async def post_batch(
        self,
        packages: List[PostPackage],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Post multiple packages to Twitter"""
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
        
        logger.info(f"Twitter batch complete: {summary['successful']}/{summary['total']} successful")
        
        return summary
    
    def is_configured(self) -> bool:
        """Check if Twitter client is properly configured"""
        return self.client is not None and self.api is not None
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        if not self.api:
            return {"error": "Not configured"}
        
        try:
            limits = self.api.rate_limit_status()
            return {
                "remaining": limits.get("resources", {}).get("statuses", {}).get("/statuses/update", {}).get("remaining", "unknown")
            }
        except Exception as e:
            return {"error": str(e)}
