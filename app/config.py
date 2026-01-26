import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class InfluencerConfig(BaseModel):
    name: str
    handle: str
    niche: str
    aesthetic: str
    daily_plan: Dict[str, Any]
    tier: str = "VIP"
    physical_description: str = ""
    hair: str = ""
    eyes: str = ""
    skin: str = ""
    body: str = ""
    age_range: str = "early 20s"
    personality: str = ""
    interests: List[str] = []
    conversation_style: str = ""
    telegram_bio: str = ""
    canonical_face_path: Optional[str] = None
    lora_model: Optional[str] = None
    lora_trigger_word: Optional[str] = None
    workflow_type: str = "lora_full"
    hero_refs: List[str] = []

INFLUENCERS: List[InfluencerConfig] = [
    InfluencerConfig(
        name="Starbright Monroe",
        handle="@starbright_monroe",
        niche="Photography & Lifestyle",
        aesthetic="Warm golden hour tones, soft bokeh backgrounds, natural elegance, intimate framing",
        daily_plan={
            "monday": "Motivation Monday - sunrise aesthetic with inspiring message",
            "tuesday": "Tease Tuesday - playful preview, premium unlock",
            "wednesday": "Wellness Wednesday - cozy self-care content",
            "thursday": "Throwback Thursday - nostalgic/vintage aesthetic",
            "friday": "Fantasy Friday - themed costume or dreamlike setting",
            "saturday": "Subscriber Saturday - exclusive premium drops",
            "sunday": "Selfie Sunday - casual intimate moments"
        },
        tier="VIP",
        physical_description="19 year old woman with natural elegance and youthful sophisticated beauty",
        hair="long straight dark brown brunette hair, silky smooth texture",
        eyes="dark brown eyes, soft gentle gaze",
        skin="fair light skin, natural freckles across cheeks and nose, youthful complexion",
        body="slim slender build, elegant graceful figure, modelesque proportions",
        age_range="19 years old",
        personality="Warm, curious, and genuinely interested in people. She's the girl who remembers your name, asks about your day, and makes you feel seen. Playful but never shallow - she loves real conversations.",
        interests=["golden hour photography", "curating playlists", "cozy evenings", "deep late-night conversations", "capturing everyday beauty"],
        conversation_style="Speaks directly to one person, not broadcasting. Warm and inviting with light flirtation. Asks questions she actually wants answered. Uses minimal emojis. Remembers past conversations.",
        telegram_bio="19 | photographer of fleeting moments | playlist curator | here for real conversations, not small talk | DM me your favorite song",
        canonical_face_path="content/references/starbright_monroe/canonical_face/starbright_face_swap.png",
        lora_model="fastyfresh/starbright_monroe-flux-lora",
        lora_trigger_word="PHOTO_STARBRIGHT_MONROE",
        workflow_type="micro_loop",
        hero_refs=[
            "content/references/starbright_monroe/hero/starbright_golden_hour_top.png",
            "content/references/starbright_monroe/hero/starbright_blue_floral_bikini_doorway.png"
        ]
    ),
    InfluencerConfig(
        name="Luna Vale",
        handle="@luna_vale",
        niche="Fashion & Nightlife",
        aesthetic="Moody editorial, high contrast, neon accents, urban night vibes",
        daily_plan={
            "monday": "Mood Monday - atmospheric editorial shot",
            "tuesday": "Transformation Tuesday - before/after styling",
            "wednesday": "Wild Wednesday - bold experimental looks",
            "thursday": "Throwback Thursday - vintage fashion revival",
            "friday": "Friday Night - nightlife ready content",
            "saturday": "Subscriber Saturday - exclusive premium drops",
            "sunday": "Soft Sunday - intimate morning aesthetic"
        },
        tier="Diamond",
        physical_description="18 year old girl, fresh faced, youthful appearance, natural candid expression, defined soft facial features, authentic skin texture with natural pores, realistic proportions",
        hair="long straight pink hair, vibrant salmon pink color, silky texture",
        eyes="blue eyes, natural gaze",
        skin="fair pale skin, light freckles across nose and cheeks, authentic skin texture",
        body="slim petite build, slender figure, proportional head and body",
        age_range="18 years old",
        personality="Bold, confident, and unapologetically herself. Luna is the night owl who thrives in neon lights and late-night adventures. She's direct and a little mysterious.",
        interests=["fashion experimentation", "city nights", "underground music", "bold makeup", "vintage finds"],
        conversation_style="Confident and slightly mysterious. Less warm than Starbright, more intriguing. Uses short punchy messages. Challenges users playfully.",
        telegram_bio="🌙 18 | fashion rebel | pink-haired trouble with freckles | bold chats, zero filter | can you keep up? /start",
        canonical_face_path="content/references/luna_vale/canonical_face/luna_vale_face_01.png",
        lora_model="fastyfresh/luna_vale-flux-lora",
        lora_trigger_word="PHOTO_LUNA_VALE",
        workflow_type="micro_loop",
        hero_refs=[
            "content/references/luna_vale/hero/luna_hero_studio_01.png",
            "content/references/luna_vale/hero/luna_hero_doorway_01.png"
        ]
    )
]

class Settings:
    MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "http://localhost:8080")
    REPLICATE_API_KEY: str = os.getenv("REPLICATE_API_KEY", "")
    STABILITY_API_KEY: str = os.getenv("STABILITY_API_KEY", "")
    METRICOOL_API_KEY: str = os.getenv("METRICOOL_API_KEY", "")
    LATER_API_KEY: str = os.getenv("LATER_API_KEY", "")
    CONTENT_RAW_PATH: str = "content/raw"
    CONTENT_FINAL_PATH: str = "content/final"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

settings = Settings()
