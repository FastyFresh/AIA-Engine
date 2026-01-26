"""
TwitterOAuth2Agent - Twitter/X posting via OAuth 2.0 PKCE + OAuth 1.0a for media

Uses OAuth 2.0 for text tweets and OAuth 1.0a for media uploads (required by Twitter).
"""

import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

logger = logging.getLogger(__name__)

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    logger.warning("Tweepy not installed. Twitter posting will be disabled.")

TOKEN_FILE = Path("data/twitter_tokens.json")
POST_COUNTER_FILE = Path("data/post_counter.json")

# Import dynamic hashtag optimizer
from app.agents.hashtag_optimizer import generate_hashtags_with_grok, format_hashtags, _fallback_hashtags

INFLUENCER_CTA = {
    "starbright_monroe": "dfans.co/starbrightnight",
    "luna_vale": "dfans.co/lunavale",
}

from app.agents.fanvue_cta_optimizer import get_optimizer

def get_post_count(influencer: str) -> int:
    """Get current post count for influencer"""
    try:
        if POST_COUNTER_FILE.exists():
            data = json.loads(POST_COUNTER_FILE.read_text())
            return data.get(influencer, 0)
    except Exception:
        pass
    return 0

def increment_post_count(influencer: str) -> int:
    """Increment and return new post count for influencer"""
    try:
        POST_COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if POST_COUNTER_FILE.exists():
            data = json.loads(POST_COUNTER_FILE.read_text())
        count = data.get(influencer, 0) + 1
        data[influencer] = count
        POST_COUNTER_FILE.write_text(json.dumps(data, indent=2))
        return count
    except Exception as e:
        logger.warning(f"Failed to update post counter: {e}")
        return 1

def should_include_cta(influencer: str) -> bool:
    """Return True if CTA should be included (every 3rd post)"""
    count = get_post_count(influencer)
    return (count + 1) % 3 == 0


class TwitterOAuth2Agent:
    """
    Twitter poster using OAuth 2.0 PKCE flow for text + OAuth 1.0a for media uploads.
    
    Setup flow:
    1. User visits /api/twitter/auth to start authorization
    2. User authorizes on Twitter
    3. Callback receives tokens and stores them
    4. Agent can then post on behalf of user
    """
    
    def __init__(self):
        # OAuth 2.0 credentials (for text tweets)
        self.client_id = os.getenv("TWITTER_CLIENT_ID")
        self.client_secret = os.getenv("TWITTER_CLIENT_SECRET")
        self.redirect_uri = self._get_redirect_uri()
        self.scopes = ["tweet.read", "tweet.write", "users.read", "offline.access"]
        
        # OAuth 1.0a credentials (for media uploads)
        self.consumer_key = os.getenv("TWITTER_API_KEY")
        self.consumer_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token_1a = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        self.oauth2_handler = None
        self.client = None  # OAuth 2.0 client
        self.api_v1 = None  # OAuth 1.0a API for media
        self.client_v1 = None  # OAuth 1.0a client for tweets
        self.access_token = None
        self.refresh_token = None
        self.user_info = None
        
        self._load_tokens()
        
        if self.access_token:
            self._initialize_client()
        
        # Initialize OAuth 1.0a for media uploads
        self._initialize_oauth1a()
        
        logger.info(f"TwitterOAuth2Agent initialized (configured: {self.is_configured()}, media_ready: {self.is_media_ready()})")
    
    def _get_redirect_uri(self) -> str:
        """Get the callback URI for OAuth"""
        domain = os.getenv("REPLIT_DEV_DOMAIN")
        if domain:
            return f"https://{domain}/api/twitter/callback"
        return "http://localhost:5000/api/twitter/callback"
    
    def _initialize_oauth1a(self):
        """Initialize OAuth 1.0a for media uploads"""
        if not TWEEPY_AVAILABLE:
            return
        
        if all([self.consumer_key, self.consumer_secret, self.access_token_1a, self.access_token_secret]):
            try:
                auth = tweepy.OAuth1UserHandler(
                    self.consumer_key,
                    self.consumer_secret,
                    self.access_token_1a,
                    self.access_token_secret
                )
                self.api_v1 = tweepy.API(auth)
                
                # Also create OAuth 1.0a client for tweet creation with media
                self.client_v1 = tweepy.Client(
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    access_token=self.access_token_1a,
                    access_token_secret=self.access_token_secret
                )
                
                logger.info("OAuth 1.0a initialized for media uploads")
            except Exception as e:
                logger.error(f"Failed to initialize OAuth 1.0a: {e}")
                self.api_v1 = None
                self.client_v1 = None
        else:
            missing = []
            if not self.consumer_key:
                missing.append("TWITTER_API_KEY")
            if not self.consumer_secret:
                missing.append("TWITTER_API_SECRET")
            if not self.access_token_1a:
                missing.append("TWITTER_ACCESS_TOKEN")
            if not self.access_token_secret:
                missing.append("TWITTER_ACCESS_TOKEN_SECRET")
            logger.warning(f"OAuth 1.0a credentials incomplete. Missing: {missing}")
    
    def _load_tokens(self):
        """Load saved tokens from file"""
        if TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    self.user_info = data.get("user_info")
                    logger.info(f"Loaded Twitter tokens for user: {self.user_info}")
            except Exception as e:
                logger.error(f"Failed to load tokens: {e}")
    
    def _save_tokens(self):
        """Save tokens to file"""
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(TOKEN_FILE, 'w') as f:
                json.dump({
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "user_info": self.user_info,
                    "updated_at": datetime.now().isoformat()
                }, f, indent=2)
            logger.info("Twitter tokens saved")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
    
    def _initialize_client(self):
        """Initialize the Tweepy client with access token"""
        if not TWEEPY_AVAILABLE or not self.access_token:
            return
        
        try:
            self.client = tweepy.Client(self.access_token)
            logger.info("Twitter client initialized with OAuth 2.0")
        except Exception as e:
            logger.error(f"Failed to initialize client: {e}")
            self.client = None
    
    def get_authorization_url(self) -> Dict[str, Any]:
        """Generate OAuth 2.0 authorization URL for user to visit"""
        if not TWEEPY_AVAILABLE:
            return {"error": "Tweepy not installed"}
        
        if not self.client_id:
            return {"error": "TWITTER_CLIENT_ID not configured"}
        
        try:
            self.oauth2_handler = tweepy.OAuth2UserHandler(
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scopes,
                client_secret=self.client_secret
            )
            
            auth_url = self.oauth2_handler.get_authorization_url()
            
            logger.info(f"Generated auth URL: {auth_url[:50]}...")
            
            return {
                "status": "success",
                "auth_url": auth_url,
                "redirect_uri": self.redirect_uri,
                "message": "Visit the auth_url to authorize the app"
            }
        except Exception as e:
            logger.error(f"Failed to generate auth URL: {e}")
            return {"error": str(e)}
    
    def handle_callback(self, callback_url: str) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for tokens"""
        if not self.oauth2_handler:
            return {"error": "OAuth flow not started. Call get_authorization_url first."}
        
        try:
            token = self.oauth2_handler.fetch_token(callback_url)
            
            self.access_token = token.get("access_token")
            self.refresh_token = token.get("refresh_token")
            
            self._initialize_client()
            
            if self.client:
                try:
                    me = self.client.get_me(user_auth=False)
                    if me and me.data:
                        self.user_info = {
                            "id": me.data.id,
                            "username": me.data.username,
                            "name": me.data.name
                        }
                except Exception as e:
                    logger.warning(f"Could not fetch user info: {e}")
            
            self._save_tokens()
            
            logger.info(f"OAuth successful! User: {self.user_info}")
            
            return {
                "status": "success",
                "message": "Authorization successful!",
                "user": self.user_info,
                "has_refresh_token": self.refresh_token is not None
            }
            
        except Exception as e:
            logger.error(f"OAuth callback failed: {e}")
            return {"error": str(e)}
    
    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            return {"error": "No refresh token available"}
        
        if not self.client_id:
            return {"error": "TWITTER_CLIENT_ID not configured"}
        
        try:
            import requests
            
            token_url = "https://api.twitter.com/2/oauth2/token"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id
            }
            
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens.get("access_token")
                self.refresh_token = tokens.get("refresh_token", self.refresh_token)
                
                self._initialize_client()
                self._save_tokens()
                
                logger.info("Access token refreshed")
                return {"status": "success", "message": "Token refreshed"}
            else:
                logger.error(f"Token refresh failed: {response.text}")
                return {"error": f"Refresh failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return {"error": str(e)}
    
    async def post_text(self, text: str) -> Dict[str, Any]:
        """Post a text-only tweet"""
        if not self.client:
            if self.access_token:
                self._initialize_client()
            if not self.client:
                return {"error": "Not authorized. Visit /api/twitter/auth first."}
        
        try:
            response = self.client.create_tweet(text=text, user_auth=False)
            
            tweet_id = response.data.get("id") if response.data else None
            tweet_url = f"https://twitter.com/i/status/{tweet_id}" if tweet_id else None
            
            logger.info(f"Posted tweet: {tweet_url}")
            
            return {
                "status": "success",
                "tweet_id": tweet_id,
                "tweet_url": tweet_url,
                "text": text,
                "posted_at": datetime.now().isoformat()
            }
        except tweepy.errors.Unauthorized:
            logger.warning("Token expired, attempting refresh...")
            refresh_result = self.refresh_access_token()
            if refresh_result.get("status") == "success":
                return await self.post_text(text)
            return {"error": "Token expired and refresh failed"}
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return {"error": str(e)}
    
    async def post_with_media(
        self, 
        text: str, 
        media_path: str,
        influencer: str = "starbright_monroe"
    ) -> Dict[str, Any]:
        """
        Post a tweet with media (video/image) using OAuth 1.0a
        
        Args:
            text: Tweet text
            media_path: Path to video or image file
            influencer: Influencer name for hashtags/CTA
        """
        if not self.api_v1 or not self.client_v1:
            return {
                "error": "Media upload not configured. Missing OAuth 1.0a credentials.",
                "missing": "TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET"
            }
        
        media_file = Path(media_path)
        if not media_file.exists():
            return {"error": f"Media file not found: {media_path}"}
        
        try:
            is_video = media_file.suffix.lower() in ['.mp4', '.mov', '.avi', '.webm']
            file_size = media_file.stat().st_size
            
            logger.info(f"Uploading {'video' if is_video else 'image'}: {media_file.name} ({file_size / 1024:.1f} KB)")
            
            # Upload media using v1.1 API
            if is_video:
                # Chunked upload for videos
                media = self.api_v1.media_upload(
                    filename=str(media_file),
                    chunked=True,
                    media_category="tweet_video"
                )
            else:
                # Simple upload for images
                media = self.api_v1.media_upload(filename=str(media_file))
            
            media_id = media.media_id
            logger.info(f"Media uploaded successfully. Media ID: {media_id}")
            
            # Create tweet with media using OAuth 1.0a client
            response = self.client_v1.create_tweet(
                text=text,
                media_ids=[media_id]
            )
            
            tweet_id = response.data.get("id") if response.data else None
            tweet_url = f"https://twitter.com/i/status/{tweet_id}" if tweet_id else None
            
            logger.info(f"Posted tweet with media: {tweet_url}")
            
            post_count = increment_post_count(influencer)
            logger.info(f"Post count for {influencer}: {post_count}")
            
            return {
                "status": "success",
                "tweet_id": tweet_id,
                "tweet_url": tweet_url,
                "text": text,
                "media_id": str(media_id),
                "media_type": "video" if is_video else "image",
                "posted_at": datetime.now().isoformat(),
                "post_count": post_count,
                "cta_included": should_include_cta(influencer)
            }
            
        except tweepy.errors.Forbidden as e:
            logger.error(f"Forbidden error: {e}")
            return {
                "error": "Permission denied. Check app permissions in Twitter Developer Portal.",
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to post with media: {e}")
            return {"error": str(e)}
    
    def compose_post_sync(
        self,
        caption: str,
        influencer: str = "starbright_monroe",
        include_cta: bool = True,
        include_hashtags: bool = True,
        hashtags_list: list = None
    ) -> str:
        """
        Compose a complete tweet with caption, CTA, and pre-generated hashtags (sync version)
        
        Args:
            caption: The main caption text
            influencer: Influencer name for config
            include_cta: Whether to include Fanvue CTA
            include_hashtags: Whether to include hashtags
            hashtags_list: Pre-generated list of hashtags
        
        Returns:
            Complete tweet text
        """
        parts = [caption.strip()]
        
        if include_cta:
            cta = INFLUENCER_CTA.get(influencer, INFLUENCER_CTA["starbright_monroe"])
            parts.append(f"\n{cta}")
        
        if include_hashtags and hashtags_list:
            parts.append("\n" + " ".join(hashtags_list))
        
        return "".join(parts)
    
    async def compose_post(
        self,
        caption: str,
        influencer: str = "starbright_monroe",
        include_cta: bool = True,
        include_hashtags: bool = True,
        media_filename: str = None,
        max_hashtags: int = 5,
        use_dynamic_cta: bool = True,
        cta_category: str = "soft_tease",
        force_cta: bool = False
    ) -> Dict[str, Any]:
        """
        Compose a complete tweet with caption, CTA, and dynamic AI-optimized hashtags
        
        Args:
            caption: The main caption text
            influencer: Influencer name for config
            include_cta: Whether to include Fanvue CTA (subject to rotation)
            include_hashtags: Whether to include hashtags
            media_filename: Filename for context-aware hashtag generation
            max_hashtags: Maximum number of hashtags
            use_dynamic_cta: Whether to use AI-optimized CTA from optimizer
            cta_category: CTA category (soft_tease, curiosity, direct, exclusive)
            force_cta: If True, always include CTA regardless of rotation
        
        Returns:
            Dict with composed_text, hashtags, and metadata
        """
        parts = [caption.strip()]
        hashtag_result = None
        cta_used = None
        
        cta_included = force_cta or (include_cta and should_include_cta(influencer))
        
        if cta_included:
            dfans_link = INFLUENCER_CTA.get(influencer, INFLUENCER_CTA["starbright_monroe"])
            if use_dynamic_cta:
                try:
                    optimizer = get_optimizer(influencer)
                    cta_text = optimizer.get_next_cta(cta_category)
                    cta_used = f"{cta_text}\n{dfans_link}"
                except Exception as e:
                    logger.warning(f"CTA optimizer error, using fallback: {e}")
                    cta_used = dfans_link
            else:
                cta_used = dfans_link
            parts.append(cta_used)
        
        if include_hashtags:
            hashtag_result = await generate_hashtags_with_grok(
                caption=caption,
                influencer=influencer,
                media_filename=media_filename,
                max_tags=max_hashtags
            )
            if hashtag_result.get("hashtags"):
                parts.append(" ".join(hashtag_result["hashtags"]))
        
        composed_text = "\n".join(parts)
        
        return {
            "composed_text": composed_text,
            "character_count": len(composed_text),
            "within_limit": len(composed_text) <= 280,
            "hashtags": hashtag_result.get("hashtags", []) if hashtag_result else [],
            "hashtag_source": hashtag_result.get("source", "none") if hashtag_result else "none",
            "hashtag_strategy": hashtag_result.get("strategy", "") if hashtag_result else "",
            "influencer": influencer,
            "cta_used": cta_used,
            "cta_source": "optimizer" if use_dynamic_cta and cta_used else "static"
        }
    
    async def post_full_package(
        self,
        caption: str,
        media_path: str,
        influencer: str = "starbright_monroe",
        include_cta: bool = True,
        include_hashtags: bool = True,
        force_cta: bool = False
    ) -> Dict[str, Any]:
        """
        Post a complete package: video + caption + CTA + dynamic AI-optimized hashtags
        
        Args:
            caption: Main caption text
            media_path: Path to video/image file
            influencer: Influencer name
            include_cta: Include Fanvue link
            include_hashtags: Include dynamic hashtags
        """
        media_filename = Path(media_path).name if media_path else None
        
        compose_result = await self.compose_post(
            caption=caption,
            influencer=influencer,
            include_cta=include_cta,
            include_hashtags=include_hashtags,
            media_filename=media_filename,
            max_hashtags=5,
            force_cta=force_cta
        )
        
        full_text = compose_result["composed_text"]
        hashtags = compose_result.get("hashtags", [])
        
        if len(full_text) > 280 and len(hashtags) > 3:
            compose_result = await self.compose_post(
                caption=caption,
                influencer=influencer,
                include_cta=include_cta,
                include_hashtags=include_hashtags,
                media_filename=media_filename,
                max_hashtags=3,
                force_cta=force_cta
            )
            full_text = compose_result["composed_text"]
            hashtags = compose_result.get("hashtags", [])
        
        if len(full_text) > 280:
            full_text = self.compose_post_sync(
                caption=caption,
                influencer=influencer,
                include_cta=include_cta,
                include_hashtags=False
            )
            hashtags = []
        
        result = await self.post_with_media(
            text=full_text,
            media_path=media_path,
            influencer=influencer
        )
        
        if result.get("status") == "success":
            result["composed_text"] = full_text
            result["influencer"] = influencer
            result["hashtags"] = hashtags
            result["hashtag_source"] = compose_result.get("hashtag_source", "none")
        
        return result
    
    def is_configured(self) -> bool:
        """Check if the agent is ready for text posting (OAuth 2.0)"""
        return self.client is not None
    
    def is_media_ready(self) -> bool:
        """Check if the agent is ready for media uploads (OAuth 1.0a)"""
        return self.api_v1 is not None and self.client_v1 is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Twitter agent"""
        return {
            "client_id_configured": bool(self.client_id),
            "authorized": self.is_configured(),
            "user": self.user_info,
            "has_refresh_token": bool(self.refresh_token),
            "redirect_uri": self.redirect_uri,
            "media_upload_ready": self.is_media_ready(),
            "oauth1a_configured": all([
                self.consumer_key, 
                self.consumer_secret, 
                self.access_token_1a, 
                self.access_token_secret
            ])
        }
    
    def disconnect(self) -> Dict[str, Any]:
        """Clear stored tokens and disconnect"""
        self.access_token = None
        self.refresh_token = None
        self.user_info = None
        self.client = None
        
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
        
        return {"status": "disconnected", "message": "Twitter authorization cleared"}
