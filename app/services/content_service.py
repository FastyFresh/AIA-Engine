from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import logging
import shutil
import os

from app.config import InfluencerConfig, settings

logger = logging.getLogger(__name__)

MAX_RAW_IMAGES = 5

USE_LLM_CAPTIONS = True
DEFAULT_LLM_PROVIDER = "anthropic"


@dataclass
class PromptConfig:
    base_prompt: str
    lighting: str
    style_tokens: List[str]
    negative_prompt: str


class ContentService:
    
    PERSONA_PROMPTS = {
        "Starbright Monroe": (
            "19 year old woman, youthful natural elegance, sophisticated beauty, "
            "long straight dark brown brunette hair, dark brown eyes, soft gentle gaze, "
            "fair light skin with natural freckles across cheeks and nose, youthful complexion, "
            "slim slender elegant graceful figure, lifestyle influencer, "
            "wearing elegant stylish clothing"
        ),
        "Luna Vale": (
            "young woman in her early 20s, striking edgy beauty, confident expression, "
            "long straight pink hair vibrant salmon pink color, blue-green eyes, "
            "fair pale skin with light freckles porcelain complexion, "
            "slim petite slender elegant figure, fashion influencer, "
            "stylish trendy outfit"
        )
    }
    
    LIGHTING_CONTEXTS = {
        "morning": "soft morning golden hour light through window, warm tones, cozy atmosphere",
        "afternoon": "natural bright daylight, outdoor setting, vibrant colors",
        "evening": "warm evening ambient lighting, relaxed intimate setting",
        "night": "moody neon lights, urban night scene, high contrast"
    }
    
    REALISM_TOKENS = [
        "RAW photo", "35mm photograph", "natural skin texture with pores",
        "photorealistic", "professional photography", "8k uhd", 
        "dslr quality", "subtle film grain", "sharp focus"
    ]
    
    NEGATIVE_PROMPT = (
        "(lowres, low quality, worst quality:1.2), (text:1.2), watermark, "
        "painting, drawing, illustration, glitch, deformed, mutated, cross-eyed, "
        "ugly, disfigured, cartoon, anime, CGI, 3D render, digital art, "
        "artificial, plastic skin, airbrushed, multiple people, two people"
    )
    
    def __init__(self):
        self.content_raw_path = settings.CONTENT_RAW_PATH
        self.content_final_path = settings.CONTENT_FINAL_PATH
        self.references_path = "content/references"
        self.archives_path = "content/archives"
    
    def get_output_dir(self, influencer: InfluencerConfig, stage: str = "raw") -> str:
        influencer_folder = self._get_influencer_folder(influencer)
        base_path = self.content_raw_path if stage == "raw" else self.content_final_path
        return f"{base_path}/{influencer_folder}"
    
    def auto_archive_images(self, influencer: InfluencerConfig, max_keep: int = MAX_RAW_IMAGES) -> int:
        influencer_folder = self._get_influencer_folder(influencer)
        raw_dir = Path(f"{self.content_raw_path}/{influencer_folder}")
        archive_dir = Path(f"{self.archives_path}/{influencer_folder}")
        
        if not raw_dir.exists():
            return 0
        
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        images = []
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            images.extend(list(raw_dir.glob(f"*{ext}")))
        
        images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        archived_count = 0
        if len(images) > max_keep:
            to_archive = images[max_keep:]
            for img in to_archive:
                dest = archive_dir / img.name
                shutil.move(str(img), str(dest))
                archived_count += 1
                logger.info(f"Archived: {img.name}")
        
        if archived_count > 0:
            logger.info(f"Archived {archived_count} images for {influencer.name}")
        
        return archived_count
    
    def get_filename_prefix(self, influencer: InfluencerConfig, slot: str) -> str:
        influencer_folder = self._get_influencer_folder(influencer)
        return f"{influencer_folder}_{slot}"
    
    def _get_influencer_folder(self, influencer: InfluencerConfig) -> str:
        return influencer.name.lower().replace(" ", "_")
    
    def get_reference_image(self, influencer: InfluencerConfig) -> Optional[str]:
        influencer_folder = self._get_influencer_folder(influencer)
        ref_dir = Path(f"{self.references_path}/{influencer_folder}")
        
        if not ref_dir.exists():
            return None
        
        priority_patterns = ["*face*", "*selfie*", "*closeup*", "*portrait*"]
        valid_extensions = [".png", ".jpg", ".jpeg", ".webp"]
        
        for pattern in priority_patterns:
            for ext in valid_extensions:
                candidates = list(ref_dir.glob(f"{pattern}{ext}"))
                if candidates:
                    logger.info(f"Using priority reference: {candidates[0]}")
                    return str(candidates[0])
        
        for ext in valid_extensions:
            candidates = list(ref_dir.glob(f"*{ext}"))
            if candidates:
                return str(candidates[0])
        
        return None
    
    def get_all_reference_images(self, influencer: InfluencerConfig) -> List[str]:
        influencer_folder = self._get_influencer_folder(influencer)
        ref_dir = Path(f"{self.references_path}/{influencer_folder}")
        
        if not ref_dir.exists():
            return []
        
        images = []
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            images.extend([str(p) for p in ref_dir.glob(f"*{ext}")])
        
        return images
    
    def build_prompt(
        self,
        influencer: InfluencerConfig,
        description: str,
        identity_context: Optional[Dict[str, Any]] = None
    ) -> str:
        persona = self._build_persona_from_config(influencer)
        
        lighting = self._detect_lighting(description)
        
        full_prompt = (
            f"RAW photo, 35mm photograph, {persona}, "
            f"{lighting}, {description}, "
            f"{influencer.aesthetic}, "
            f"natural skin texture with pores, photorealistic, "
            f"professional photography, instagram aesthetic, "
            f"8k uhd, dslr quality, subtle film grain, "
            f"sharp focus on face, bokeh background"
        )
        
        return full_prompt
    
    def _build_persona_from_config(self, influencer: InfluencerConfig) -> str:
        if influencer.hair or influencer.body:
            parts = [f"young woman in her {influencer.age_range}"]
            
            if influencer.physical_description:
                parts.append(influencer.physical_description)
            
            if influencer.hair:
                parts.append(influencer.hair)
            
            if influencer.eyes:
                parts.append(influencer.eyes)
            
            if influencer.skin:
                parts.append(influencer.skin)
            
            if influencer.body:
                parts.append(influencer.body)
            
            parts.append(f"{influencer.niche.lower()} influencer")
            
            return ", ".join(parts)
        
        return self.PERSONA_PROMPTS.get(
            influencer.name,
            "beautiful young woman, natural beauty"
        )
    
    def build_simple_prompt(self, description: str) -> str:
        tokens = ", ".join(self.REALISM_TOKENS[:5])
        return f"{description}, {tokens}"
    
    def get_negative_prompt(self, include_face_artifacts: bool = True) -> str:
        base = self.NEGATIVE_PROMPT
        if include_face_artifacts:
            base += ", ghost face, duplicate face, two heads, double head"
        return base
    
    def _detect_lighting(self, description: str) -> str:
        description_lower = description.lower()
        
        for key, lighting in self.LIGHTING_CONTEXTS.items():
            if key in description_lower:
                return lighting
        
        return "natural soft lighting, professional studio"
    
    def generate_caption(
        self,
        influencer: InfluencerConfig,
        description: str,
        identity_context: Optional[Dict[str, Any]] = None
    ) -> str:
        return self._generate_template_caption(influencer, description, identity_context)
    
    def _generate_template_caption(
        self,
        influencer: InfluencerConfig,
        description: str,
        identity_context: Optional[Dict[str, Any]] = None
    ) -> str:
        if identity_context:
            themes = identity_context.get("content_themes", [])
            hashtags = " ".join([f"#{theme.replace(' ', '')}" for theme in themes[:3]])
        else:
            hashtags = f"#{influencer.niche.replace(' ', '').lower()}"
        
        return f"[Auto-generated caption for: {description}] {hashtags}"
    
    async def generate_caption_async(
        self,
        influencer: InfluencerConfig,
        description: str,
        identity_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        fallback_caption = self._generate_template_caption(influencer, description, identity_context)
        
        if not USE_LLM_CAPTIONS:
            return {
                "caption": fallback_caption,
                "source": "template",
                "llm_used": False
            }
        
        try:
            from app.tools.llm_client import LLMClient, PromptConfig as LLMPromptConfig
            
            llm_client = LLMClient()
            
            voice_tone = "warm and encouraging" if "wellness" in influencer.niche.lower() else "bold and confident"
            if identity_context:
                voice_tone = identity_context.get("voice_tone", voice_tone)
            
            themes = []
            if identity_context:
                themes = identity_context.get("content_themes", [])
            hashtag_suggestions = ", ".join([f"#{t.replace(' ', '')}" for t in themes[:5]]) if themes else f"#{influencer.niche.replace(' ', '').lower()}"
            
            system_prompt = f"""You are {influencer.name}, a {influencer.niche} influencer on Instagram. 
Your voice is {voice_tone}. Your aesthetic is {influencer.aesthetic}.

Write authentic, engaging Instagram captions that:
- Sound natural and human (not robotic or salesy)
- Match the influencer's personality and niche
- Include 3-5 relevant hashtags at the end
- Are 1-3 sentences (concise but impactful)
- Never use phrases like "living my best life" or overly generic influencer clichés

Do NOT include any quotation marks around the caption. Just write the caption directly."""

            user_prompt = f"""Write an Instagram caption for this post:

Content: {description}

Suggested hashtags to consider: {hashtag_suggestions}

Remember: Be authentic to {influencer.name}'s voice. Keep it concise."""

            prompt_config = LLMPromptConfig(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=200,
                temperature=0.8
            )
            
            response = await llm_client.generate_text(
                prompt_config=prompt_config,
                provider=DEFAULT_LLM_PROVIDER,
                fallback_text=fallback_caption
            )
            
            if response.success:
                caption = response.content.strip().strip('"\'')
                logger.info(f"LLM caption generated: provider={response.provider}, latency={response.latency_ms:.0f}ms")
                return {
                    "caption": caption,
                    "source": "llm",
                    "llm_used": True,
                    "provider": response.provider,
                    "latency_ms": response.latency_ms
                }
            else:
                logger.warning(f"LLM caption failed: {response.error}, using fallback")
                return {
                    "caption": fallback_caption,
                    "source": "template",
                    "llm_used": False,
                    "llm_error": response.error
                }
                
        except Exception as e:
            logger.error(f"Caption generation error: {e}")
            return {
                "caption": fallback_caption,
                "source": "template",
                "llm_used": False,
                "llm_error": str(e)
            }
    
    def get_daily_slots(self, influencer: InfluencerConfig) -> Dict[str, str]:
        slots = {}
        for slot, description in influencer.daily_plan.items():
            if slot != "fanvue_exclusive":
                slots[slot] = description
        return slots
    
    def get_reference_status(self) -> Dict[str, Any]:
        status = {}
        ref_path = Path(self.references_path)
        
        if ref_path.exists():
            for influencer_dir in ref_path.iterdir():
                if influencer_dir.is_dir():
                    images = []
                    for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
                        images.extend(list(influencer_dir.glob(ext)))
                    
                    status[influencer_dir.name] = {
                        "has_reference": len(images) > 0,
                        "image_count": len(images),
                        "images": [str(img) for img in images]
                    }
        
        return status
