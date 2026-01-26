"""
Image Generator Interface - Abstract base for all image generation services

This provides a unified interface for different image generation backends:
- Fal.ai Seedream (SFW, primary)
- Replicate Seedream (SFW, fallback)
- Venice.ai (NSFW)
- ModelsLab (NSFW)
- RunPod/Local (NSFW)

Each provider implements the same interface, making it easy to swap backends
or use multiple providers based on content requirements.
"""

import os
import base64
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class ContentRating(Enum):
    """Content rating for generated images"""
    SFW = "sfw"
    NSFW = "nsfw"


@dataclass
class GenerationResult:
    """Result from an image generation request"""
    success: bool
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    generation_time_seconds: float = 0.0
    provider: str = ""
    

@dataclass
class GenerationRequest:
    """Request for image generation"""
    prompt: str
    negative_prompt: str = ""
    width: int = 1024
    height: int = 1536
    num_inference_steps: int = 30
    guidance_scale: float = 7.5
    seed: Optional[int] = None
    reference_images: Optional[List[str]] = None
    content_rating: ContentRating = ContentRating.SFW


class ImageGeneratorInterface(ABC):
    """
    Abstract base class for image generation services.
    
    All image generators must implement:
    - generate(): Core generation method
    - build_prompt(): Prompt construction with identity preservation
    - supports_references(): Whether provider supports reference images
    - get_provider_name(): Human-readable provider name
    - get_content_rating(): SFW or NSFW capability
    """
    
    def __init__(self, influencer_id: str = "starbright_monroe"):
        self.influencer_id = influencer_id
        self.output_dir = Path("content/generated")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate an image from the request.
        
        Args:
            request: GenerationRequest with prompt and parameters
            
        Returns:
            GenerationResult with image path or error
        """
        pass
    
    @abstractmethod
    def build_prompt(
        self,
        scene: str,
        outfit: str,
        pose: str = "standing confidently",
        lighting: str = "soft natural lighting",
        additional: str = ""
    ) -> str:
        """
        Build a prompt with character identity preservation.
        
        Args:
            scene: Background/environment description
            outfit: Clothing description
            pose: Body positioning
            lighting: Lighting setup
            additional: Extra prompt elements
            
        Returns:
            Complete prompt string
        """
        pass
    
    @abstractmethod
    def supports_references(self) -> bool:
        """Whether this provider supports reference image conditioning"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get human-readable provider name"""
        pass
    
    @abstractmethod
    def get_content_rating(self) -> ContentRating:
        """Get content rating capability (SFW or NSFW)"""
        pass
    
    def encode_image_base64(self, path: str) -> str:
        """Encode image to base64 data URI - shared utility"""
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        
        ext = Path(path).suffix.lower()
        mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp"
        }.get(ext, "image/png")
        
        return f"data:{mime};base64,{data}"
    
    def save_image(self, image_data: bytes, filename: str) -> str:
        """Save image data to output directory - shared utility"""
        output_path = self.output_dir / filename
        with open(output_path, "wb") as f:
            f.write(image_data)
        return str(output_path)
    
    async def download_image(self, url: str) -> bytes:
        """Download image from URL - shared utility"""
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content


class ImageGeneratorFactory:
    """
    Factory for creating image generators based on requirements.
    
    Usage:
        generator = ImageGeneratorFactory.get_generator(
            influencer_id="starbright_monroe",
            content_rating=ContentRating.SFW
        )
        result = await generator.generate(request)
    """
    
    _providers: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, provider_class: type):
        """Register a provider class"""
        cls._providers[name] = provider_class
        logger.info(f"Registered image provider: {name}")
    
    @classmethod
    def get_generator(
        cls,
        influencer_id: str = "starbright_monroe",
        content_rating: ContentRating = ContentRating.SFW,
        provider: str = None
    ) -> ImageGeneratorInterface:
        """
        Get an appropriate image generator.
        
        Args:
            influencer_id: Which influencer persona
            content_rating: SFW or NSFW content needed
            provider: Specific provider name (optional)
            
        Returns:
            ImageGeneratorInterface implementation
        """
        if provider and provider in cls._providers:
            return cls._providers[provider](influencer_id)
        
        if content_rating == ContentRating.SFW:
            if "fal_seedream" in cls._providers:
                return cls._providers["fal_seedream"](influencer_id)
            elif "replicate_seedream" in cls._providers:
                return cls._providers["replicate_seedream"](influencer_id)
        else:
            if "venice" in cls._providers:
                return cls._providers["venice"](influencer_id)
            elif "modelslab" in cls._providers:
                return cls._providers["modelslab"](influencer_id)
            elif "runpod" in cls._providers:
                return cls._providers["runpod"](influencer_id)
        
        raise ValueError(f"No provider available for {content_rating.value} content")
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered providers"""
        return list(cls._providers.keys())
    
    @classmethod
    def get_providers_by_rating(cls, content_rating: ContentRating) -> List[str]:
        """Get providers that support a specific content rating"""
        matching = []
        for name, provider_class in cls._providers.items():
            try:
                instance = provider_class()
                if instance.get_content_rating() == content_rating:
                    matching.append(name)
            except Exception:
                pass
        return matching
