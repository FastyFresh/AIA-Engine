"""
CaptionAgent - Template-based caption generation for social media posts

Generates platform-specific captions using template banks with variable substitution.
"""

import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.pipeline_config import get_caption_templates, CAPTION_TEMPLATES

logger = logging.getLogger(__name__)


class CaptionAgent:
    """
    Generates captions for social media posts using templates.
    
    Features:
    - Platform-specific template banks
    - Variable substitution (color, mood, time of day, etc.)
    - Randomization for variety
    - Hashtag generation (optional)
    """
    
    def __init__(self):
        self.custom_templates: Dict[str, List[str]] = {}
        logger.info("CaptionAgent initialized")
    
    def generate_caption(
        self,
        platform: str,
        metadata: Dict[str, Any] = None,
        use_hashtags: bool = True
    ) -> str:
        """
        Generate a caption for a specific platform.
        
        Args:
            platform: Target platform (reddit, twitter, instagram, tiktok)
            metadata: Image/content metadata for variable substitution
            use_hashtags: Whether to append relevant hashtags
        """
        metadata = metadata or {}
        
        templates = self._get_templates(platform)
        template = random.choice(templates)
        
        variables = self._prepare_variables(metadata)
        
        try:
            caption = template.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing variable {e} in template, using fallback")
            caption = template
            for key, value in variables.items():
                caption = caption.replace(f"{{{key}}}", value)
        
        if use_hashtags and platform in ["instagram", "tiktok", "instagram_manual", "tiktok_manual"]:
            hashtags = self._generate_hashtags(platform, metadata)
            caption = f"{caption}\n\n{hashtags}"
        
        return caption
    
    def generate_reddit_title(
        self,
        metadata: Dict[str, Any] = None,
        subreddit: str = ""
    ) -> str:
        """Generate a Reddit-appropriate title"""
        metadata = metadata or {}
        
        title_templates = [
            "New {outfit_color} look 💕",
            "Feeling {mood} today 😊",
            "Just trying something new 💗",
            "Be honest - thoughts? 🥺",
            "{time_of_day} vibes ✨",
            "Rate this look?",
            "Hi everyone 👋",
            "Trying to be more confident 💕"
        ]
        
        template = random.choice(title_templates)
        variables = self._prepare_variables(metadata)
        
        try:
            title = template.format(**variables)
        except KeyError:
            title = template
            for key, value in variables.items():
                title = title.replace(f"{{{key}}}", value)
        
        return title
    
    def generate_twitter_text(
        self,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Generate a Twitter-appropriate text (under 280 chars)"""
        caption = self.generate_caption("twitter", metadata, use_hashtags=False)
        
        if len(caption) > 250:
            caption = caption[:247] + "..."
        
        return caption
    
    def _get_templates(self, platform: str) -> List[str]:
        """Get templates for a platform"""
        if platform in self.custom_templates:
            return self.custom_templates[platform]
        
        platform_key = platform.replace("_manual", "")
        
        if platform_key == "instagram":
            return CAPTION_TEMPLATES.instagram
        elif platform_key == "twitter":
            return CAPTION_TEMPLATES.twitter
        elif platform_key == "tiktok":
            return CAPTION_TEMPLATES.tiktok
        else:
            return CAPTION_TEMPLATES.reddit
    
    def _prepare_variables(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Prepare template variables from metadata"""
        now = datetime.now()
        hour = now.hour
        
        if 5 <= hour < 12:
            time_of_day = "Morning"
        elif 12 <= hour < 17:
            time_of_day = "Afternoon"
        elif 17 <= hour < 21:
            time_of_day = "Evening"
        else:
            time_of_day = "Late night"
        
        colors = ["pink", "white", "black", "blue", "lavender", "red", "purple"]
        moods = ["happy", "confident", "cozy", "playful", "relaxed", "cute"]
        activities = ["chilling", "relaxing", "vibing", "working out", "getting ready"]
        scenarios = ["you see me at the cafe", "we make eye contact", "I smile at you"]
        
        return {
            "outfit_color": metadata.get("outfit_color", metadata.get("color", random.choice(colors))),
            "color": metadata.get("color", random.choice(colors)),
            "mood": metadata.get("mood", random.choice(moods)),
            "time_of_day": metadata.get("time_of_day", time_of_day),
            "activity": metadata.get("activity", random.choice(activities)),
            "scenario": metadata.get("scenario", random.choice(scenarios)),
            "pose": metadata.get("pose", "casual"),
            "background": metadata.get("background", "")
        }
    
    def _generate_hashtags(
        self,
        platform: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Generate relevant hashtags"""
        base_hashtags = ["#selfie", "#ootd", "#lifestyle"]
        
        mood = metadata.get("mood", "")
        if mood:
            base_hashtags.append(f"#{mood}")
        
        if platform in ["instagram", "instagram_manual"]:
            base_hashtags.extend(["#instagood", "#photography", "#model"])
        elif platform in ["tiktok", "tiktok_manual"]:
            base_hashtags.extend(["#fyp", "#foryou", "#viral"])
        
        selected = random.sample(base_hashtags, min(5, len(base_hashtags)))
        return " ".join(selected)
    
    def add_custom_templates(self, platform: str, templates: List[str]):
        """Add custom templates for a platform"""
        self.custom_templates[platform] = templates
        logger.info(f"Added {len(templates)} custom templates for {platform}")
