"""
Central Pipeline Configuration for AIA Engine v1

This module contains all configuration for the daily automation pipeline including:
- Platform quotas and posting schedules
- Style rotation profiles
- Caption templates per platform
- Subreddit targeting
- Quality thresholds for auto-curation
"""

import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import time


class QualityThresholds(BaseModel):
    """Thresholds for automatic content curation"""
    auto_approve: float = 0.85
    pending_min: float = 0.0  # All images go to pending for manual review
    auto_reject_below: float = 0.0  # Disabled - no auto-rejection


class PostingWindow(BaseModel):
    """Time window for posting content"""
    start_hour: int = 9
    end_hour: int = 22
    peak_hours: List[int] = [12, 15, 18, 21]


class PlatformQuotas(BaseModel):
    """Daily posting quotas per platform"""
    reddit: int = 6
    twitter: int = 4
    instagram_manual: int = 2
    tiktok_manual: int = 1


class StyleProfile(BaseModel):
    """Style configuration for content generation"""
    name: str
    poses: List[str]
    outfits: List[str]
    backgrounds: List[str]
    mood: str


class SubredditConfig(BaseModel):
    """Configuration for Reddit posting"""
    name: str
    flair: Optional[str] = None
    title_style: str = "casual"
    nsfw: bool = False
    min_karma: int = 0
    post_frequency: str = "daily"


class CaptionTemplates(BaseModel):
    """Caption templates per platform"""
    reddit: List[str] = [
        "New {outfit_color} look 💕 what do you think?",
        "Feeling {mood} today 😊",
        "Just trying something new 💗",
        "Be honest… does this look okay? 🥺",
        "{time_of_day} vibes ✨",
        "Rate this look 1-10? 💖"
    ]
    twitter: List[str] = [
        "Trying a new look today 💗",
        "Feeling {mood} 😊",
        "{time_of_day} selfie ✨",
        "What do you think? 💕",
        "Just because 💖",
        "Hi there 👋💕"
    ]
    instagram: List[str] = [
        "Be honest… does this look okay on me? 💗",
        "{time_of_day} mood ✨",
        "Feeling {mood} today 💕",
        "Just vibing 🌟",
        "Rate this 1-10 💖",
        "What's your favorite? 💗"
    ]
    tiktok: List[str] = [
        "POV: {scenario} 💕",
        "When {scenario} ✨",
        "Just {activity} things 💗",
        "Rate this look 💖",
        "{time_of_day} check ✨"
    ]


MICRO_MOVEMENT_PROMPTS = {
    "micro_sway": "Create a short animated video using the reference image. Keep the background, lighting, camera angle, and subject exactly the same. Animate one subtle micro-movement: a slow, gentle full-body sway, a slight natural movement in her hair, and a soft slight smile. Smooth, minimal, loopable motion.",
    "hair_breeze": "Generate a short animated video using the reference image. Keep everything identical except the model's hair, which should move softly as if touched by a light indoor breeze. Add a gentle slight smile to her expression. Background stays still, smooth and loopable.",
    "weight_shift": "Create an animated video using the reference image. Maintain the exact background and appearance but animate a very slight weight shift — a small one-inch forward or backward adjustment, as if she settles into a comfortable stance with a soft slight smile. Subtle, smooth, loopable.",
    "micro_smile": "Create a subtle animated video from the reference image. Begin with the exact expression shown, then animate a warm soft smile forming naturally. The movement is slow, minimal, and loopable. Background and body remain still.",
    "shoulder_adjust": "Generate a short animation using the reference image. Keep the environment and pose the same but animate a tiny natural movement: a slight adjustment of her shoulder or arm with a gentle slight smile. Very subtle, clean, loopable.",
    "head_tilt": "Create a short looping video using the reference image. The subject remains in the same environment, but performs a soft, slow head tilt of just a few degrees with a gentle slight smile before returning. Minimal motion, natural, smooth loop.",
    "breathing": "Generate a subtle animated video using the reference image. Keep everything identical but animate a very soft breathing motion in her chest and shoulders with a relaxed slight smile. Almost imperceptible but clearly alive. Smooth, gentle, loopable motion.",
    "hair_tuck": "Create a short animated clip using the reference image. Animate a tiny flick or micro-movement near her hair, as if she lightly adjusts or tucks a strand with a soft slight smile. Movement must remain small and elegant. Background stays still.",
    "lean_forward": "Generate a short animated video from the reference image. Keep all details the same but animate a slow, subtle lean forward by one or two inches with a warm slight smile, then return. Natural, minimal, smooth, loopable.",
    "soft_blink": "Create a short animated video using the reference image. Animate a slow, natural blink, a tiny shift of her gaze, and a gentle slight smile. Keep the background, pose, and lighting unchanged. Motion should be minimal and loop-friendly."
}


class InfluencerPipelineConfig(BaseModel):
    """Pipeline-specific configuration per influencer"""
    influencer_name: str
    quotas: PlatformQuotas = PlatformQuotas()
    posting_window: PostingWindow = PostingWindow()
    quality_thresholds: QualityThresholds = QualityThresholds()
    style_profiles: List[StyleProfile] = []
    target_subreddits: List[SubredditConfig] = []
    enabled_platforms: List[str] = ["reddit", "twitter", "instagram_manual", "tiktok_manual"]
    face_swap_all: bool = False  # Disabled by default - face swap is optional during approval
    workflow_type: str = "lora_full"  # "lora_full" or "micro_loop"
    micro_movement_prompts: List[str] = list(MICRO_MOVEMENT_PROMPTS.keys())  # Available movement types


STYLE_PROFILES = {
    "casual_lifestyle": StyleProfile(
        name="casual_lifestyle",
        poses=["casual sitting", "standing relaxed", "leaning against wall", "coffee shop pose"],
        outfits=["casual dress", "jeans and top", "sundress", "cozy sweater"],
        backgrounds=["cafe interior", "bedroom", "living room", "outdoor patio"],
        mood="relaxed"
    ),
    "glamour": StyleProfile(
        name="glamour",
        poses=["confident standing", "over shoulder look", "sitting elegantly", "mirror selfie"],
        outfits=["evening dress", "cocktail dress", "elegant outfit", "formal wear"],
        backgrounds=["upscale interior", "city lights", "elegant room", "studio backdrop"],
        mood="confident"
    ),
    "fitness": StyleProfile(
        name="fitness",
        poses=["workout pose", "stretching", "active stance", "gym selfie"],
        outfits=["activewear", "sports bra and leggings", "workout outfit", "athletic wear"],
        backgrounds=["gym", "yoga studio", "outdoor trail", "home workout space"],
        mood="energetic"
    ),
    "beach_summer": StyleProfile(
        name="beach_summer",
        poses=["beach standing", "sitting on sand", "walking on beach", "poolside relaxing"],
        outfits=["bikini", "swimsuit", "beach cover-up", "summer dress"],
        backgrounds=["beach", "pool", "tropical resort", "oceanside"],
        mood="carefree"
    )
}


DEFAULT_SUBREDDITS = [
    SubredditConfig(name="selfie", title_style="casual", nsfw=False),
    SubredditConfig(name="FreeCompliments", title_style="friendly", nsfw=False),
    SubredditConfig(name="SFWNextDoorGirls", title_style="casual", nsfw=False),
    SubredditConfig(name="Faces", title_style="simple", nsfw=False),
]


PIPELINE_CONFIGS: Dict[str, InfluencerPipelineConfig] = {
    "starbright_monroe": InfluencerPipelineConfig(
        influencer_name="Starbright Monroe",
        quotas=PlatformQuotas(reddit=6, twitter=4, instagram_manual=2, tiktok_manual=1),
        quality_thresholds=QualityThresholds(auto_approve=0.85, pending_min=0.0, auto_reject_below=0.0),
        style_profiles=[
            STYLE_PROFILES["casual_lifestyle"],
            STYLE_PROFILES["glamour"]
        ],
        target_subreddits=DEFAULT_SUBREDDITS,
        face_swap_all=False,
        workflow_type="micro_loop",
        micro_movement_prompts=["micro_sway", "hair_breeze", "breathing", "soft_blink", "head_tilt", "micro_smile"]
    ),
    "luna_vale": InfluencerPipelineConfig(
        influencer_name="Luna Vale",
        quotas=PlatformQuotas(reddit=4, twitter=3, instagram_manual=2, tiktok_manual=1),
        quality_thresholds=QualityThresholds(auto_approve=0.85, pending_min=0.0, auto_reject_below=0.0),
        style_profiles=[
            STYLE_PROFILES["glamour"],
            STYLE_PROFILES["casual_lifestyle"]
        ],
        target_subreddits=DEFAULT_SUBREDDITS,
        face_swap_all=False,
        workflow_type="micro_loop",
        micro_movement_prompts=["micro_sway", "hair_breeze", "breathing", "soft_blink", "head_tilt"]
    )
}


CAPTION_TEMPLATES = CaptionTemplates()


class PipelineSettings:
    """Global pipeline settings"""
    DRY_RUN: bool = os.getenv("PIPELINE_DRY_RUN", "false").lower() == "true"
    
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USERNAME: str = os.getenv("REDDIT_USERNAME", "")
    REDDIT_PASSWORD: str = os.getenv("REDDIT_PASSWORD", "")
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "AIA-Engine/1.0")
    
    TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
    TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
    TWITTER_ACCESS_SECRET: str = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
    
    POST_PACKAGES_PATH: str = "content/post_packages"
    MANUAL_QUEUE_PATH: str = "content/manual_queue"
    
    MIN_INTERVAL_BETWEEN_POSTS_MINUTES: int = 30
    MAX_POSTS_PER_SUBREDDIT_PER_DAY: int = 2


pipeline_settings = PipelineSettings()


def get_pipeline_config(influencer_handle: str) -> InfluencerPipelineConfig:
    """Get pipeline configuration for an influencer by handle"""
    handle = influencer_handle.replace("@", "").lower()
    return PIPELINE_CONFIGS.get(handle, PIPELINE_CONFIGS["starbright_monroe"])


def get_caption_templates(platform: str) -> List[str]:
    """Get caption templates for a specific platform"""
    return getattr(CAPTION_TEMPLATES, platform, CAPTION_TEMPLATES.reddit)
