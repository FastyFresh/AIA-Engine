"""
Prompt Builder - Centralized Prompt Construction

Single source of truth for:
- Identity descriptions (per influencer)
- Camera settings (Canon EOS R5, 85mm f/1.4)
- Hyper-realism settings (visible pores, natural skin texture)
- Quality settings (8K ultra detailed)

Used by both FalSeedreamService (primary) and Seedream4Service (fallback).
"""

from typing import Dict, Optional, List
import json
import random
from pathlib import Path


CAMERA_SETTINGS = "Shot on Canon EOS R5, 85mm f/1.4 lens"
SKIN_TEXTURE = "natural skin texture with visible pores"
QUALITY_SETTINGS = "8K ultra detailed, cinematic lighting"
HYPERREAL_SKIN = "natural skin texture with visible pores, fine skin detail, slight natural skin imperfections, photorealistic skin tones, no plastic skin, no airbrushed, no over-smoothed, no beauty filter"
HYPERREAL_QUALITY = "8K ultra detailed, cinematic color grading, professional fashion photography"

CONSISTENCY_BACKGROUNDS = {
    "luxury_apartment": "modern luxury apartment studio with neutral tones, floor-to-ceiling windows, minimalist decor, soft natural daylight",
    "studio_white": "professional photography studio with pure white seamless backdrop, soft diffused lighting",
    "studio_dark": "professional photography studio with dark charcoal backdrop, dramatic side lighting",
    "bedroom": "modern luxury bedroom with soft ambient lighting, neutral tones, elegant decor",
}

CONSISTENCY_NEGATIVE_PROMPT = "no earrings, no jewelry, no accessories on ears, no piercings, no hoop earrings, no stud earrings"


INFLUENCER_IDENTITIES = {
    "starbright_monroe": {
        "name": "Starbright Monroe",
        "identity": (
            "very pale porcelain ivory white skin, "
            "straight sleek dark brown hair (not wavy, not curly), "
            "warm olive-brown eyes, natural freckles across nose and cheeks, "
            "extremely thin slender petite body with very narrow tiny waist, "
            "slim narrow hips, long thin slender legs, delicate small frame, size 0 figure, "
            "very small flat chest, tiny A-cup breasts almost flat, minimal bust, petite chest matching body reference exactly"
        ),
        "negative_prompt_additions": "large breasts, big breasts, busty, prominent bust, enhanced chest, voluptuous, curvy chest, cleavage, exaggerated chest, big bust, medium breasts, C-cup, D-cup, augmented",
        "face_ref": "content/references/starbright_monroe/starbright_face_reference_v3.webp",
        "body_ref": "content/references/starbright_monroe/body_reference.webp",
        "body_ref_back": "content/references/starbright_monroe/body_reference_back_1.webp",
        "output_dir": "content/generated/starbright_monroe",
    },
    "luna_vale": {
        "name": "Luna Vale",
        "identity": (
            "fair pale skin with subtle freckles across nose and cheeks, "
            "long straight cotton candy pink hair parted in middle, "
            "striking grey-blue eyes with long dark lashes, thick natural eyebrows, "
            "soft rounded face with defined cheekbones, full pouty natural lips, "
            "slim petite body with feminine curves, small waist, "
            "youthful delicate features, natural beauty with minimal makeup look"
        ),
        "face_ref": "content/references/luna_vale/luna_face_canonical.png",
        "body_ref": "content/references/luna_vale/luna_body_reference.png",
        "body_ref_back": None,
        "output_dir": "content/generated/luna_vale",
    }
}


class PromptBuilder:
    """
    Centralized prompt construction for consistent image generation.
    
    Provides standardized prompts with:
    - Character identity preservation
    - Hyper-realistic photography settings
    - Consistent quality parameters
    """
    
    def __init__(self, influencer_id: str = "starbright_monroe"):
        """Initialize with a specific influencer configuration."""
        if influencer_id not in INFLUENCER_IDENTITIES:
            raise ValueError(f"Unknown influencer: {influencer_id}. Available: {list(INFLUENCER_IDENTITIES.keys())}")
        self.influencer_id = influencer_id
        self.config = INFLUENCER_IDENTITIES[influencer_id]
    
    @property
    def identity(self) -> str:
        """Get the identity description for the current influencer."""
        return self.config["identity"]
    
    @property
    def face_ref(self) -> str:
        """Get face reference path."""
        return self.config["face_ref"]
    
    @property
    def body_ref(self) -> str:
        """Get body reference path."""
        return self.config["body_ref"]
    
    @property
    def body_ref_back(self) -> Optional[str]:
        """Get back-facing body reference path."""
        return self.config.get("body_ref_back")
    
    @property
    def output_dir(self) -> str:
        """Get output directory for generated images."""
        return self.config["output_dir"]
    
    def build_fal_prompt(
        self,
        scene: str,
        outfit: str,
        pose: str = "standing confidently",
        lighting: str = "soft natural lighting",
        additional: str = ""
    ) -> str:
        """
        Build a prompt for fal.ai Seedream 4.5 with direct identity description.
        
        Uses Replicate-style prompting where reference images are passed separately
        and the model uses them automatically without Figure 1/2 references.
        
        Args:
            scene: Background/environment description
            outfit: Clothing description
            pose: Body positioning
            lighting: Lighting setup
            additional: Extra prompt elements
        
        Returns:
            Formatted prompt string
        """
        prompt = (
            "Use the woman from Figure 1 (face reference) and Figure 2 (body reference). "
            f"Maintain her EXACT facial features: {self.identity}. "
            f"She is {pose}, wearing {outfit}, in {scene}, {lighting}. "
            f"{CAMERA_SETTINGS}, {SKIN_TEXTURE}, {QUALITY_SETTINGS}"
        )
        
        if additional:
            prompt += f". {additional}"
        
        return prompt
    
    def build_research_prompt(self, narrative_prompt: str) -> str:
        """
        Build a prompt from a research-derived narrative.
        
        Uses Figure 1/2 references with explicit facial identity preservation instructions
        as recommended by SEEDream 4.5 documentation for character consistency.
        
        Args:
            narrative_prompt: The narrative prompt from research agent
        
        Returns:
            Full prompt with identity and camera settings
        """
        identity_prefix = (
            "Use the woman from Figure 1 (face reference) and Figure 2 (body reference). "
            f"STRICTLY preserve her EXACT facial features from Figure 1: {self.identity}. "
            "Keep the same face shape, eyes, nose, lips, natural freckles, and real skin texture with visible pores - not airbrushed or smoothed. "
            "STRICTLY match Figure 2 body proportions: petite slender frame, slim narrow waist, small natural bust, no exaggerated curves. "
        )
        
        camera_suffix = (
            f" {CAMERA_SETTINGS}, {SKIN_TEXTURE}, {QUALITY_SETTINGS}."
        )
        
        return identity_prefix + narrative_prompt + camera_suffix
    
    def build_consistency_prompt(
        self,
        pose: str,
        outfit: str,
        background: str = "luxury_apartment",
        lighting: str = "soft natural daylight"
    ) -> tuple[str, str]:
        """
        Build a prompt for consistency mode with locked background and no accessories.
        
        Args:
            pose: Exact pose description (passed directly, not mixed with narrative)
            outfit: Clothing description
            background: Background preset key or custom description
            lighting: Lighting setup
        
        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        scene = CONSISTENCY_BACKGROUNDS.get(background, background)
        
        prompt = (
            "Use the woman from Figure 1 (face reference) and Figure 2 (body reference). "
            f"Maintain her EXACT facial features: {self.identity}. "
            f"{pose}, wearing {outfit}. "
            f"Setting: {scene}, {lighting}. "
            f"No earrings, no jewelry, no ear accessories. "
            f"{CAMERA_SETTINGS}, {SKIN_TEXTURE}, {QUALITY_SETTINGS}."
        )
        
        return prompt, CONSISTENCY_NEGATIVE_PROMPT
    
    def build_consistency_from_narrative(
        self,
        narrative_prompt: str,
        background: str = "luxury_apartment",
        lighting: str = "soft studio lighting from above"
    ) -> tuple[str, str]:
        """
        Build a prompt from narrative with locked background override.
        
        Takes a full narrative prompt from the library and replaces
        any setting/background with a consistent preset. Also applies
        the accessory suppression negative prompt.
        
        Args:
            narrative_prompt: Full narrative prompt from library
            background: Background preset key or custom description
            lighting: Lighting setup
        
        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        import re
        
        scene = CONSISTENCY_BACKGROUNDS.get(background, background)
        
        modified_prompt = narrative_prompt
        setting_patterns = [
            r'The setting is [^.]+\.',
            r'Setting: [^.]+\.',
            r'in an? [^,.]+ setting[^.]*\.',
            r'in an? [^,.]+ background[^.]*\.',
            r'with a [^,.]+ backdrop[^.]*\.',
            r'outdoor [^,.]+ with [^.]+\.',
            r'indoor [^,.]+ with [^.]+\.',
        ]
        
        for pattern in setting_patterns:
            modified_prompt = re.sub(pattern, '', modified_prompt, flags=re.IGNORECASE)
        
        modified_prompt = re.sub(r'\s+', ' ', modified_prompt).strip()
        
        identity_prefix = (
            "Use the woman from Figure 1 (face reference) and Figure 2 (body reference). "
            f"Maintain her EXACT facial features: {self.identity}. "
        )
        
        setting_clause = f" Setting: {scene}, {lighting}. No earrings, no jewelry, no ear accessories."
        camera_suffix = f" {CAMERA_SETTINGS}, {SKIN_TEXTURE}, {QUALITY_SETTINGS}."
        
        full_prompt = identity_prefix + modified_prompt + setting_clause + camera_suffix
        
        return full_prompt, CONSISTENCY_NEGATIVE_PROMPT
    
    def build_replicate_prompt(
        self,
        scene: str,
        outfit: str,
        pose: str = "full body portrait",
        lighting: str = "soft diffused natural lighting",
        accessories: str = "none",
        additional: str = "",
        hyperreal: bool = True
    ) -> str:
        """
        Build a prompt for Replicate Seedream 4.5 (fallback service).
        
        Args:
            scene: Background/environment description
            outfit: Clothing description
            pose: Body positioning
            lighting: Lighting setup
            accessories: Accessory description or preset
            additional: Extra prompt elements
            hyperreal: Enable hyper-realism mode
        
        Returns:
            Formatted prompt string
        """
        accessory_options = {
            "none": "no jewelry, no earrings, no accessories",
            "minimal": "small stud earrings only",
            "earrings": "small hoop earrings",
            "necklace": "delicate gold necklace, no earrings",
            "full": "small hoop earrings, delicate necklace"
        }
        
        accessory_text = accessory_options.get(accessories, accessories)
        
        identity_text = f"young woman model, {self.identity}"
        
        if hyperreal:
            prompt_parts = [
                f"shot on Canon EOS R5, 85mm f/1.4 lens, shallow depth of field",
                pose,
                identity_text,
                accessory_text,
                outfit,
                scene,
                lighting,
                HYPERREAL_SKIN,
                HYPERREAL_QUALITY
            ]
        else:
            prompt_parts = [
                "Professional fashion photography",
                pose,
                identity_text,
                accessory_text,
                outfit,
                scene,
                lighting,
                "8k ultra detailed"
            ]
        
        if additional:
            prompt_parts.append(additional)
        
        return ", ".join(prompt_parts)
    
    def build_unified_prompt(
        self,
        pose_text: str,
        expression_text: str,
        outfit: str,
        background_description: str = ""
    ) -> str:
        """
        Build a prompt for the UnifiedContentAgent.
        
        Args:
            pose_text: Pose direction from PoseExpressionAgent
            expression_text: Expression from PoseExpressionAgent
            outfit: Clothing description
            background_description: Background from BackgroundAgent
        
        Returns:
            Formatted prompt string
        """
        identity_text = f"hyperrealistic beautiful young woman, {self.identity}"
        
        return (
            f"POSE DIRECTION: The model MUST be {pose_text} with {expression_text}. "
            f"Hyperrealistic magazine-quality fashion photography, stunning full body portrait, "
            f"{identity_text}, wearing {outfit}, {background_description}, "
            f"8k ultra HD, photorealistic skin texture with subtle imperfections, "
            f"cinematic lighting, professional studio quality, sharp focus, "
            f"alluring and captivating mood, the pose is critical - model must follow the pose direction exactly"
        )
    
    @classmethod
    def get_influencer_ids(cls) -> list:
        """Get list of available influencer IDs."""
        return list(INFLUENCER_IDENTITIES.keys())
    
    @classmethod
    def get_influencer_config(cls, influencer_id: str) -> Dict:
        """Get full configuration for an influencer."""
        if influencer_id not in INFLUENCER_IDENTITIES:
            raise ValueError(f"Unknown influencer: {influencer_id}")
        return INFLUENCER_IDENTITIES[influencer_id]


prompt_builder = PromptBuilder()


class LunaModularPromptBuilder:
    """
    Luna-specific modular prompt builder following the V1 spec.
    
    Assembles scene-focused prompts from modular blocks:
    - Outfit (tiered by phase)
    - Background
    - Vibe
    - Camera & Lighting
    
    Identity is handled by Seedream 4.5 reference images, not text.
    """
    
    def __init__(self, config_path: str = "content/luna_prompt_config.json"):
        """Load Luna configuration from JSON."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.character = self.config["character"]
        self.modules = self.config["modules"]
        self.prompt_builder = PromptBuilder("luna_vale")
        
    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Luna config not found: {self.config_path}")
    
    def reload_config(self):
        """Reload configuration from file."""
        self.config = self._load_config()
        self.character = self.config["character"]
        self.modules = self.config["modules"]
    
    @property
    def face_ref(self) -> str:
        """Get face reference path."""
        return self.character.get("face_ref", self.prompt_builder.face_ref)
    
    @property
    def body_ref(self) -> str:
        """Get body reference path."""
        return self.character.get("body_ref", self.prompt_builder.body_ref)
    
    @property
    def negative_prompt(self) -> str:
        """Get the negative prompt."""
        return self.character.get("negative_prompt", "")
    
    def get_outfit_tier(self, tier: int = 1) -> List[str]:
        """Get outfit options for a specific tier."""
        tier_key = f"tier_{tier}"
        return self.modules["outfit"].get(tier_key, self.modules["outfit"]["tier_1"])
    
    def get_backgrounds(self, category: str = "safe_high_reach") -> List[str]:
        """Get backgrounds from a category."""
        return self.modules["background"].get(category, self.modules["background"]["safe_high_reach"])
    
    def get_vibes(self, category: str = "core") -> List[str]:
        """Get vibes from a category."""
        return self.modules["vibe"].get(category, self.modules["vibe"]["core"])
    
    def get_camera_lighting(self) -> str:
        """Get the camera & lighting block."""
        return self.modules["camera_lighting"]
    
    def sample_outfit(self, tier: int = 1) -> str:
        """Randomly sample an outfit from the specified tier."""
        options = self.get_outfit_tier(tier)
        return random.choice(options)
    
    def sample_background(self, category: str = "safe_high_reach") -> str:
        """Randomly sample a background from the specified category."""
        options = self.get_backgrounds(category)
        return random.choice(options)
    
    def sample_vibe(self, category: str = "core") -> str:
        """Randomly sample a vibe from the specified category."""
        options = self.get_vibes(category)
        return random.choice(options)
    
    def assemble_prompt(
        self,
        outfit: Optional[str] = None,
        background: Optional[str] = None,
        vibe: Optional[str] = None,
        outfit_tier: int = 1,
        background_category: str = "safe_high_reach",
        vibe_category: str = "core"
    ) -> tuple[str, str]:
        """
        Assemble a scene-focused prompt from modular blocks.
        
        Identity is handled by Seedream 4.5 reference images.
        This method assembles outfit/background/vibe into a scene prompt.
        
        Args:
            outfit: Specific outfit text, or None to sample
            background: Specific background text, or None to sample
            vibe: Specific vibe text, or None to sample
            outfit_tier: Tier to sample from if outfit is None
            background_category: Category to sample from if background is None
            vibe_category: Category to sample from if vibe is None
        
        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        final_outfit = outfit or self.sample_outfit(outfit_tier)
        final_background = background or self.sample_background(background_category)
        final_vibe = vibe or self.sample_vibe(vibe_category)
        camera_lighting = self.get_camera_lighting()
        
        prompt = self.prompt_builder.build_fal_prompt(
            scene=final_background,
            outfit=final_outfit,
            pose=final_vibe,
            lighting=camera_lighting
        )
        
        return prompt, self.negative_prompt
    
    def generate_batch_prompts(
        self,
        count: int = 5,
        outfit_tier: int = 1,
        fixed_outfit: Optional[str] = None,
        background_category: str = "safe_high_reach",
        vibe_category: str = "core"
    ) -> List[tuple[str, str]]:
        """
        Generate a batch of prompts with variety.
        
        Args:
            count: Number of prompts to generate
            outfit_tier: Tier to sample outfits from
            fixed_outfit: If provided, use this outfit for all prompts (consistency)
            background_category: Background category to sample from
            vibe_category: Vibe category to sample from
        
        Returns:
            List of (positive_prompt, negative_prompt) tuples
        """
        prompts = []
        outfit = fixed_outfit or self.sample_outfit(outfit_tier)
        
        for _ in range(count):
            background = self.sample_background(background_category)
            vibe = self.sample_vibe(vibe_category)
            prompt, neg = self.assemble_prompt(
                outfit=outfit,
                background=background,
                vibe=vibe
            )
            prompts.append((prompt, neg))
        
        return prompts
    
    def get_tier_for_week(self, week: int) -> int:
        """Determine which tier to use based on week number."""
        if week <= 3:
            return 1
        elif week <= 6:
            return 2
        else:
            return 3
    
    def list_all_outfits(self) -> Dict[str, List[str]]:
        """List all outfits by tier."""
        return self.modules["outfit"]
    
    def list_all_backgrounds(self) -> Dict[str, List[str]]:
        """List all backgrounds by category."""
        return self.modules["background"]
    
    def list_all_vibes(self) -> Dict[str, List[str]]:
        """List all vibes by category."""
        return self.modules["vibe"]


luna_prompt_builder = None

def get_luna_prompt_builder() -> LunaModularPromptBuilder:
    """Get or create the Luna prompt builder singleton."""
    global luna_prompt_builder
    if luna_prompt_builder is None:
        try:
            luna_prompt_builder = LunaModularPromptBuilder()
        except FileNotFoundError:
            return None
    return luna_prompt_builder
