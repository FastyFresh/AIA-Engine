"""
Seedream 4.5 Generation Service - FALLBACK Image Generation (Replicate)

Uses ByteDance Seedream 4.5 on Replicate with multi-reference image conditioning
for consistent, hyper-realistic character generation.

SERVICE HIERARCHY:
- PRIMARY: fal_seedream_service.py (fal.ai) - faster, more reliable, cheaper
- FALLBACK: This service (Replicate) - used by UnifiedContentAgent for multi-ref

UPGRADED TO SEEDREAM 4.5 (December 2024):
- Model: bytedance/seedream-4.5 (4K support, enhanced realism)
- Resolution: 4K by default for maximum skin texture detail
- Prompt Format: Professional photography with camera specs
- Skin: Natural texture with visible pores, no plastic/airbrushed look
- References: Up to 10 reference images supported

Now uses centralized PromptBuilder for consistent identity/camera/quality settings.
"""

import os
import base64
import asyncio
import httpx
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.services.prompt_builder import PromptBuilder, INFLUENCER_IDENTITIES
from app.services.storage_manager import storage_manager

logger = logging.getLogger(__name__)

REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
SEEDREAM_MODEL = "bytedance/seedream-4.5"


class Seedream4Service:
    """
    FALLBACK service for generating hyper-realistic images using Seedream 4.5 with reference images.
    
    Uses Replicate API with multi-reference support (up to 10 images).
    For primary image generation, use FalSeedreamService instead.
    """
    
    def __init__(self, influencer_id: str = "starbright_monroe"):
        self.replicate_api_token = os.getenv("REPLICATE_API_TOKEN", "")
        self.influencer_id = influencer_id
        
        config = INFLUENCER_IDENTITIES.get(influencer_id, INFLUENCER_IDENTITIES["starbright_monroe"])
        self.output_dir = Path("content/seedream4_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.face_ref_path = config["face_ref"]
        self.body_ref_path = config["body_ref"]
        
        self.prompt_builder = PromptBuilder(influencer_id)
        
        self._version_id = None
        self.hyperreal_mode = True
        logger.info(f"Seedream 4.5 Service initialized for {influencer_id} - Hyper-Realism Mode ENABLED (FALLBACK)")
    
    async def get_model_version(self) -> str:
        """Get the latest Seedream 4.5 model version"""
        if self._version_id:
            return self._version_id
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://api.replicate.com/v1/models/{SEEDREAM_MODEL}",
                headers={"Authorization": f"Token {self.replicate_api_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self._version_id = data.get("latest_version", {}).get("id")
                logger.info(f"Using Seedream 4.5 version: {self._version_id[:20]}...")
                return self._version_id
            else:
                raise Exception(f"Failed to get model version: {response.text}")
    
    def encode_image(self, path: str) -> str:
        """Encode image to base64 data URL"""
        with open(path, "rb") as f:
            data = f.read()
        
        ext = Path(path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp"
        }
        mime = mime_types.get(ext, "image/png")
        
        return f"data:{mime};base64,{base64.b64encode(data).decode()}"
    
    def build_prompt(
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
        Build a hyper-realistic prompt using centralized PromptBuilder.
        
        Args:
            scene: Background/environment description
            outfit: Clothing description
            pose: Body positioning
            lighting: Lighting setup
            accessories: "none", "minimal", "earrings", "necklace", or specific
            additional: Extra prompt elements
            hyperreal: Enable hyper-realism mode (default True)
        """
        return self.prompt_builder.build_replicate_prompt(
            scene=scene,
            outfit=outfit,
            pose=pose,
            lighting=lighting,
            accessories=accessories,
            additional=additional,
            hyperreal=hyperreal and self.hyperreal_mode
        )
    
    def build_prompt_simple(
        self, 
        outfit: str, 
        scene: str, 
        lighting: str = "natural lighting",
        accessories: str = "none"
    ) -> str:
        """Quick prompt builder with defaults"""
        return self.build_prompt(
            scene=scene,
            outfit=outfit,
            pose="full body portrait",
            lighting=lighting,
            accessories=accessories
        )
    
    async def generate(
        self,
        prompt: str,
        face_ref: Optional[str] = None,
        body_ref: Optional[str] = None,
        aspect_ratio: str = "9:16",
        seed: Optional[int] = None,
        filename_prefix: str = "starbright",
        size: str = "4K"
    ) -> Dict[str, Any]:
        """
        Generate a hyper-realistic image using Seedream 4.5 with reference images
        
        Args:
            prompt: The generation prompt
            face_ref: Path to face reference image (uses default if None)
            body_ref: Path to body reference image (uses default if None)
            aspect_ratio: Image aspect ratio (default 9:16 for portrait)
            seed: Random seed for reproducibility
            filename_prefix: Prefix for output filename
            size: Resolution - "2K" or "4K" (default 4K for max detail)
            
        Returns:
            Dict with status, image_path, and metadata
        """
        
        if not self.replicate_api_token:
            return {"status": "error", "error": "REPLICATE_API_TOKEN not configured"}
        
        face_path = face_ref or self.face_ref_path
        body_path = body_ref or self.body_ref_path
        
        if not os.path.exists(face_path):
            return {"status": "error", "error": f"Face reference not found: {face_path}"}
        if not os.path.exists(body_path):
            return {"status": "error", "error": f"Body reference not found: {body_path}"}
        
        try:
            version = await self.get_model_version()
            
            face_b64 = self.encode_image(face_path)
            body_b64 = self.encode_image(body_path)
            
            input_data = {
                "prompt": prompt,
                "image_input": [face_b64, body_b64],
                "aspect_ratio": aspect_ratio,
                "size": size,
                "max_images": 1,
                "sequential_image_generation": "disabled"
            }
            
            if seed is not None:
                input_data["seed"] = seed
            
            logger.info(f"Seedream 4.5 generation: {size} resolution, {aspect_ratio} aspect ratio")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    REPLICATE_API_URL,
                    headers={
                        "Authorization": f"Token {self.replicate_api_token}",
                        "Content-Type": "application/json"
                    },
                    json={"version": version, "input": input_data}
                )
                
                if response.status_code not in [200, 201]:
                    return {"status": "error", "error": f"API error: {response.text}"}
                
                prediction = response.json()
                prediction_id = prediction.get("id")
                
                if not prediction_id:
                    return {"status": "error", "error": "No prediction ID returned"}
                
                logger.info(f"Started Seedream 4.5 hyper-real generation: {prediction_id}")
                
                for _ in range(150):
                    await asyncio.sleep(2)
                    
                    check_response = await client.get(
                        f"{REPLICATE_API_URL}/{prediction_id}",
                        headers={"Authorization": f"Token {self.replicate_api_token}"}
                    )
                    
                    if check_response.status_code != 200:
                        continue
                    
                    status_data = check_response.json()
                    status = status_data.get("status")
                    
                    if status == "succeeded":
                        output = status_data.get("output", [])
                        image_url = output[0] if isinstance(output, list) else output
                        
                        if image_url:
                            img_response = await client.get(image_url, timeout=60.0)
                            
                            if not storage_manager.ensure_space_for_write(estimated_size_mb=5.0):
                                logger.error("Insufficient disk space after cleanup")
                                return {"status": "error", "error": "Disk quota exceeded - cleanup performed, please retry"}
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"{filename_prefix}_{timestamp}.png"
                            save_path = self.output_dir / filename
                            
                            with open(save_path, "wb") as f:
                                f.write(img_response.content)
                            
                            logger.info(f"Saved image: {save_path}")
                            
                            return {
                                "status": "success",
                                "image_path": str(save_path),
                                "filename": filename,
                                "prediction_id": prediction_id,
                                "prompt": prompt,
                                "provider": "replicate"
                            }
                    
                    elif status in ["failed", "canceled"]:
                        error = status_data.get("error", "Generation failed")
                        logger.error(f"Seedream4 failed: {error}")
                        return {"status": "error", "error": error}
                
                return {"status": "error", "error": "Generation timed out"}
                
        except Exception as e:
            logger.error(f"Seedream4 generation error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def generate_with_background(
        self,
        prompt: str,
        face_ref: Optional[str] = None,
        body_ref: Optional[str] = None,
        background_ref: Optional[str] = None,
        aspect_ratio: str = "9:16",
        seed: Optional[int] = None,
        filename_prefix: str = "unified",
        size: str = "4K",
        negative_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate image with face, body, and optional background references.
        
        This is the primary method for the UnifiedContentAgent, supporting multi-reference generation.
        Seedream 4.5 supports up to 10 reference images for enhanced consistency.
        """
        if not self.replicate_api_token:
            return {"status": "error", "error": "REPLICATE_API_TOKEN not configured"}
        
        face_path = face_ref or self.face_ref_path
        body_path = body_ref or self.body_ref_path
        
        if not os.path.exists(face_path):
            return {"status": "error", "error": f"Face reference not found: {face_path}"}
        if not os.path.exists(body_path):
            return {"status": "error", "error": f"Body reference not found: {body_path}"}
        
        try:
            version = await self.get_model_version()
            
            face_b64 = self.encode_image(face_path)
            body_b64 = self.encode_image(body_path)
            
            image_refs = [face_b64, body_b64]
            
            if background_ref and os.path.exists(background_ref):
                bg_b64 = self.encode_image(background_ref)
                image_refs.append(bg_b64)
                logger.info(f"Using 3-reference generation with background: {background_ref}")
            
            # Default anatomical negative prompt for body consistency
            default_negative = (
                "extra limbs, extra legs, extra arms, extra fingers, missing limbs, "
                "deformed body, disproportionate body, unnatural anatomy, distorted proportions, "
                "elongated limbs, stretched arms, stretched legs, unrealistic limb length, "
                "mutated hands, fused fingers, too many fingers, missing fingers, "
                "bad anatomy, wrong anatomy, unrealistic body, mannequin, plastic skin"
            )
            
            final_negative = negative_prompt if negative_prompt else default_negative
            
            input_data = {
                "prompt": prompt,
                "image_input": image_refs,
                "aspect_ratio": aspect_ratio,
                "size": size,
                "max_images": 1,
                "sequential_image_generation": "disabled",
                "negative_prompt": final_negative,
                "disable_safety_checker": True
            }
            
            if seed is not None:
                input_data["seed"] = seed
            
            logger.info(f"Seedream 4.5 multi-ref generation: {size} resolution, {len(image_refs)} references")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    REPLICATE_API_URL,
                    headers={
                        "Authorization": f"Token {self.replicate_api_token}",
                        "Content-Type": "application/json"
                    },
                    json={"version": version, "input": input_data}
                )
                
                if response.status_code not in [200, 201]:
                    return {"status": "error", "error": f"API error: {response.text}"}
                
                prediction = response.json()
                prediction_id = prediction.get("id")
                
                if not prediction_id:
                    return {"status": "error", "error": "No prediction ID returned"}
                
                logger.info(f"Started Seedream 4.5 multi-ref generation: {prediction_id}")
                
                for _ in range(150):
                    await asyncio.sleep(2)
                    
                    check_response = await client.get(
                        f"{REPLICATE_API_URL}/{prediction_id}",
                        headers={"Authorization": f"Token {self.replicate_api_token}"}
                    )
                    
                    if check_response.status_code != 200:
                        continue
                    
                    status_data = check_response.json()
                    status = status_data.get("status")
                    
                    if status == "succeeded":
                        output = status_data.get("output", [])
                        image_url = output[0] if isinstance(output, list) else output
                        
                        if image_url:
                            img_response = await client.get(image_url, timeout=60.0)
                            
                            if not storage_manager.ensure_space_for_write(estimated_size_mb=5.0):
                                logger.error("Insufficient disk space after cleanup")
                                return {"status": "error", "error": "Disk quota exceeded - cleanup performed, please retry"}
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"{filename_prefix}_{timestamp}.png"
                            save_path = self.output_dir / filename
                            
                            with open(save_path, "wb") as f:
                                f.write(img_response.content)
                            
                            logger.info(f"Saved image: {save_path}")
                            
                            return {
                                "status": "success",
                                "image_path": str(save_path),
                                "filename": filename,
                                "prediction_id": prediction_id,
                                "prompt": prompt,
                                "refs_used": len(image_refs),
                                "provider": "replicate"
                            }
                    
                    elif status in ["failed", "canceled"]:
                        error = status_data.get("error", "Generation failed")
                        return {"status": "error", "error": error}
                
                return {"status": "error", "error": "Generation timed out"}
                
        except Exception as e:
            logger.error(f"Seedream4 3-ref generation error: {e}")
            return {"status": "error", "error": str(e)}

    async def transform_image(
        self,
        source_image_path: str,
        prompt: str,
        aspect_ratio: str = "3:4",
        seed: Optional[int] = None,
        filename_prefix: str = "transform",
        size: str = "4K",
        negative_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transform a source image into Starbright Monroe style.
        
        Uses source image as pose/scene reference, combined with face and body references
        for identity consistency.
        
        Args:
            source_image_path: Path to the image to transform
            prompt: Description of the desired output (describe pose, outfit, scene)
            aspect_ratio: Output aspect ratio
            seed: Random seed for reproducibility
            filename_prefix: Prefix for output filename
            size: Resolution - "2K" or "4K"
            negative_prompt: Things to avoid in generation
        """
        if not self.replicate_api_token:
            return {"status": "error", "error": "REPLICATE_API_TOKEN not configured"}
        
        if not os.path.exists(source_image_path):
            return {"status": "error", "error": f"Source image not found: {source_image_path}"}
        
        face_path = self.face_ref_path
        body_path = self.body_ref_path
        
        if not os.path.exists(face_path):
            return {"status": "error", "error": f"Face reference not found: {face_path}"}
        if not os.path.exists(body_path):
            return {"status": "error", "error": f"Body reference not found: {body_path}"}
        
        try:
            version = await self.get_model_version()
            
            face_b64 = self.encode_image(face_path)
            body_b64 = self.encode_image(body_path)
            
            image_refs = [face_b64, body_b64]
            
            full_prompt = prompt
            
            default_negative = (
                "extra limbs, extra legs, extra arms, extra fingers, missing limbs, "
                "deformed body, disproportionate body, unnatural anatomy, distorted proportions, "
                "elongated limbs, stretched arms, stretched legs, unrealistic limb length, "
                "mutated hands, fused fingers, too many fingers, missing fingers, "
                "bad anatomy, wrong anatomy, unrealistic body, mannequin, plastic skin"
            )
            
            final_negative = negative_prompt if negative_prompt else default_negative
            
            input_data = {
                "prompt": full_prompt,
                "image_input": image_refs,
                "aspect_ratio": aspect_ratio,
                "size": size,
                "max_images": 1,
                "sequential_image_generation": "disabled",
                "negative_prompt": final_negative,
                "disable_safety_checker": True
            }
            
            if seed is not None:
                input_data["seed"] = seed
            
            logger.info(f"Seedream 4.5 transform: {size} resolution, Figure 1=face, Figure 2=body, Figure 3=source")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    REPLICATE_API_URL,
                    headers={
                        "Authorization": f"Token {self.replicate_api_token}",
                        "Content-Type": "application/json"
                    },
                    json={"version": version, "input": input_data}
                )
                
                if response.status_code not in [200, 201]:
                    return {"status": "error", "error": f"API error: {response.text}"}
                
                prediction = response.json()
                prediction_id = prediction.get("id")
                
                if not prediction_id:
                    return {"status": "error", "error": "No prediction ID returned"}
                
                logger.info(f"Started Seedream 4.5 transform: {prediction_id}")
                
                for _ in range(150):
                    await asyncio.sleep(2)
                    
                    check_response = await client.get(
                        f"{REPLICATE_API_URL}/{prediction_id}",
                        headers={"Authorization": f"Token {self.replicate_api_token}"}
                    )
                    
                    if check_response.status_code != 200:
                        continue
                    
                    status_data = check_response.json()
                    status = status_data.get("status")
                    
                    if status == "succeeded":
                        output = status_data.get("output", [])
                        image_url = output[0] if isinstance(output, list) else output
                        
                        if image_url:
                            img_response = await client.get(image_url, timeout=60.0)
                            
                            if not storage_manager.ensure_space_for_write(estimated_size_mb=5.0):
                                logger.error("Insufficient disk space after cleanup")
                                return {"status": "error", "error": "Disk quota exceeded"}
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"{filename_prefix}_{timestamp}.png"
                            save_path = self.output_dir / filename
                            
                            with open(save_path, "wb") as f:
                                f.write(img_response.content)
                            
                            logger.info(f"Saved transformed image: {save_path}")
                            
                            return {
                                "status": "success",
                                "image_path": str(save_path),
                                "filename": filename,
                                "prediction_id": prediction_id,
                                "prompt": prompt,
                                "source_image": source_image_path,
                                "provider": "replicate"
                            }
                    
                    elif status in ["failed", "canceled"]:
                        error = status_data.get("error", "Generation failed")
                        return {"status": "error", "error": error}
                
                return {"status": "error", "error": "Generation timed out"}
                
        except Exception as e:
            logger.error(f"Seedream4 transform error: {e}")
            return {"status": "error", "error": str(e)}

    async def generate_batch(
        self,
        prompts: List[Dict[str, str]],
        aspect_ratio: str = "9:16"
    ) -> List[Dict[str, Any]]:
        """Generate multiple images"""
        results = []
        
        for i, prompt_data in enumerate(prompts):
            prompt = prompt_data.get("prompt", "")
            prefix = prompt_data.get("filename_prefix", f"batch_{i+1}")
            
            result = await self.generate(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                filename_prefix=prefix
            )
            results.append(result)
        
        return results
    
    async def generate_content(
        self,
        outfit: str,
        scene: str,
        lighting: str = "natural lighting",
        accessories: str = "none",
        filename_prefix: str = "starbright"
    ) -> Dict[str, Any]:
        """Convenience method for content generation at scale"""
        prompt = self.build_prompt_simple(outfit=outfit, scene=scene, lighting=lighting, accessories=accessories)
        return await self.generate(prompt=prompt, filename_prefix=filename_prefix)


CONTENT_PRESETS = {
    "pool_pink": {
        "outfit": "pink two-piece bikini",
        "scene": "infinity pool setting",
        "lighting": "golden hour sunset lighting"
    },
    "apartment_evening": {
        "outfit": "pink two-piece bikini",
        "scene": "minimalist modern luxury apartment",
        "lighting": "evening interior lighting, warm ambient light"
    },
    "beach_white": {
        "outfit": "white bikini",
        "scene": "tropical beach with palm trees",
        "lighting": "golden hour sunset"
    },
    "gym_black": {
        "outfit": "black sports bra and leggings",
        "scene": "modern gym",
        "lighting": "natural lighting"
    },
    "bedroom_silk": {
        "outfit": "white silk pajamas",
        "scene": "luxury bedroom",
        "lighting": "soft morning light"
    },
    "studio_blue": {
        "outfit": "blue yoga outfit",
        "scene": "minimalist white studio",
        "lighting": "professional studio lighting"
    }
}
