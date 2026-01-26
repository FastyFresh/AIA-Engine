from typing import Any, Dict, List, Optional
from datetime import datetime
from app.agents.base import BaseAgent
from app.config import InfluencerConfig, settings


class ContentGenerationAgent(BaseAgent):
    """
    Content Generation Agent - Handles prompt building and caption generation.
    
    This agent is responsible for:
    - Building optimized prompts for image generation
    - Generating captions for social media posts
    - Managing content metadata
    
    Note: Actual image generation is handled by ReferenceAgent which uses
    the Replicate API with LoRA models for consistent identity.
    """
    
    def __init__(self):
        super().__init__("ContentGenerationAgent")
    
    def build_image_prompt(
        self, 
        influencer: InfluencerConfig, 
        description: str, 
        identity_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build an optimized prompt for image generation based on influencer identity."""
        
        base_prompts = {
            "Starbright Monroe": (
                "PHOTO_STARBRIGHT_MONROE, 19 year old woman, youthful natural elegance, sophisticated beauty, "
                "long perfectly straight dark brown brunette hair, dark brown eyes, soft gentle gaze, "
                "fair light skin with natural freckles across cheeks, youthful complexion, "
                "shot on Canon EOS R5 85mm f/1.4, natural window light, shallow depth of field, "
                "real skin texture with pores, authentic candid moment, documentary photography"
            ),
            "Luna Vale": (
                "LUNAVALE, 19 year old woman, soft alternative style, striking edgy beauty, "
                "long straight pink hair, blue-green eyes, fair pale skin with light freckles, "
                "moody editorial lighting, mirror selfie aesthetic, "
                "shot on iPhone 15 Pro, natural ambient light, real skin texture, candid photo"
            )
        }
        
        base = base_prompts.get(influencer.name, "beautiful young woman, professional photography")
        
        context_additions = {
            "morning_post": "morning light, fresh and natural look, sunrise colors",
            "afternoon_post": "natural daylight, casual lifestyle moment, candid feel",
            "evening_post": "soft evening light, relaxed atmosphere, golden tones"
        }
        
        slot_context = ""
        for slot_key, addition in context_additions.items():
            if slot_key in description.lower() or any(word in description.lower() for word in slot_key.split("_")):
                slot_context = addition
                break
        
        full_prompt = f"{base}, {influencer.aesthetic}, {description}"
        if slot_context:
            full_prompt += f", {slot_context}"
            
        return full_prompt
    
    def build_negative_prompt(self) -> str:
        """Build a negative prompt to exclude unwanted elements from generation."""
        return (
            "wavy hair, curly hair, glossy skin, plastic skin, shiny skin, "
            "ugly, deformed, blurry, low quality, pixelated, watermark, text, "
            "bad anatomy, bad proportions, extra limbs, duplicate, morbid, mutilated, "
            "out of frame, poorly drawn face, mutation, poorly drawn hands, "
            "bad hands, fused fingers, too many fingers, long neck, signature"
        )
    
    def generate_caption(
        self, 
        influencer: InfluencerConfig, 
        description: str, 
        identity_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a social media caption based on content description and influencer voice."""
        identity_context = identity_context or {}
        voice = identity_context.get("voice_tone", "friendly")
        themes = identity_context.get("content_themes", [])
        hashtags = " ".join([f"#{theme.replace(' ', '')}" for theme in themes[:3]])
        
        return f"[Auto-generated caption for: {description}] {hashtags}"
    
    def get_content_metadata(
        self, 
        influencer: InfluencerConfig, 
        slot: str,
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate metadata for a piece of content."""
        return {
            "influencer": influencer.name,
            "handle": influencer.handle,
            "slot": slot,
            "created_at": datetime.now().isoformat(),
            "image_path": image_path,
            "platform_target": "instagram",
            "status": "pending_review"
        }
