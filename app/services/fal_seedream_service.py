"""
Fal.ai Seedream 4.5 Edit Service - PRIMARY Image Generation Service

Uses fal.ai's Seedream 4.5 edit endpoint with reference image conditioning
for consistent character generation with safety checker disabled.

SERVICE HIERARCHY:
- PRIMARY: This service (fal.ai) - faster, more reliable, cheaper
- FALLBACK: seedream4_service.py (Replicate) - used by UnifiedContentAgent

Key Features:
- Reference image conditioning via "Figure 1/Figure 2" system
- Safety checker can be disabled for content flexibility
- Up to 10 reference images supported
- 4K resolution output
- Automatic back-facing reference selection for rear-angle poses
"""

import os
import base64
import httpx
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from app.services.prompt_builder import PromptBuilder, INFLUENCER_IDENTITIES, CONSISTENCY_NEGATIVE_PROMPT

logger = logging.getLogger(__name__)

FAL_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"
FAL_TEXT2IMG_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/text-to-image"


class FalSeedreamService:
    """
    PRIMARY service for generating images using fal.ai Seedream 4.5 with reference conditioning.
    
    For multi-reference generation with background support, use Seedream4Service (fallback).
    """
    
    def __init__(self, influencer_id: str = "starbright_monroe"):
        self.fal_key = os.getenv("FAL_KEY", "")
        self.influencer_id = influencer_id
        
        config = INFLUENCER_IDENTITIES.get(influencer_id, INFLUENCER_IDENTITIES["starbright_monroe"])
        self.output_dir = Path(config["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.face_ref_path = config["face_ref"]
        self.body_ref_path = config["body_ref"]
        self.body_ref_back_path = config.get("body_ref_back")
        self.default_negative_prompt = config.get("negative_prompt_additions", "")
        
        self.prompt_builder = PromptBuilder(influencer_id)
        
        self._face_data_uri = None
        self._body_data_uri = None
        self._body_back_data_uri = None
        
        self.rear_angle_keywords = [
            "back to camera", "rear angle", "from behind", "looking back",
            "over shoulder", "over her shoulder", "backside", "back view",
            "behind her", "rear view", "turned away", "facing away",
            "back facing", "lying on stomach", "on her stomach"
        ]
        
        logger.info(f"Fal.ai Seedream 4.5 Service initialized for {influencer_id} (PRIMARY)")
    
    def _encode_image(self, path: str) -> str:
        """Encode image to base64 data URI"""
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
    
    def _is_rear_angle_prompt(self, prompt: str) -> bool:
        """Check if prompt describes a rear-angle or back-facing pose"""
        prompt_lower = prompt.lower()
        for keyword in self.rear_angle_keywords:
            if keyword in prompt_lower:
                logger.info(f"Detected rear-angle keyword: '{keyword}'")
                return True
        return False
    
    def _get_reference_uris(self, prompt: str = "") -> tuple:
        """Get cached reference image data URIs, selecting back refs for rear-angle poses"""
        if not self._face_data_uri and Path(self.face_ref_path).exists():
            self._face_data_uri = self._encode_image(self.face_ref_path)
            logger.info(f"Cached face reference: {len(self._face_data_uri)} chars")
        
        is_rear_angle = self._is_rear_angle_prompt(prompt) if prompt else False
        
        if is_rear_angle and self.body_ref_back_path:
            if not self._body_back_data_uri and Path(self.body_ref_back_path).exists():
                self._body_back_data_uri = self._encode_image(self.body_ref_back_path)
                logger.info(f"Cached back body reference: {len(self._body_back_data_uri)} chars")
            logger.info("Using BACK-FACING body reference for rear-angle pose")
            return self._face_data_uri, self._body_back_data_uri
        else:
            if not self._body_data_uri and Path(self.body_ref_path).exists():
                self._body_data_uri = self._encode_image(self.body_ref_path)
                logger.info(f"Cached body reference: {len(self._body_data_uri)} chars")
            return self._face_data_uri, self._body_data_uri
    
    def build_prompt(
        self,
        scene: str,
        outfit: str,
        pose: str = "standing confidently",
        lighting: str = "soft natural lighting",
        additional: str = ""
    ) -> str:
        """Build a prompt with character identity preservation using centralized PromptBuilder"""
        return self.prompt_builder.build_fal_prompt(
            scene=scene,
            outfit=outfit,
            pose=pose,
            lighting=lighting,
            additional=additional
        )
    
    async def generate_with_references(
        self,
        prompt: str,
        aspect_ratio: str = "portrait_4_3",
        output_dir: Optional[str] = None,
        filename_prefix: str = "fal_generated",
        enable_safety_checker: bool = False,
        negative_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate image using edit endpoint with reference conditioning"""
        
        if not self.fal_key:
            return {"status": "error", "error": "FAL_KEY not configured"}
        
        face_uri, body_uri = self._get_reference_uris(prompt)
        
        if not face_uri or not body_uri:
            return {"status": "error", "error": "Reference images not found"}
        
        headers = {
            "Authorization": f"Key {self.fal_key}",
            "Content-Type": "application/json"
        }
        
        # Use auto_4K for high resolution like Replicate
        # The aspect_ratio parameter is only used if not using auto_4K
        image_size = "auto_4K" if aspect_ratio in ["portrait_4_3", "portrait_16_9", "landscape_4_3", "landscape_16_9", "square"] else aspect_ratio
        
        payload = {
            "prompt": prompt,
            "image_urls": [face_uri, body_uri],
            "image_size": image_size,
            "num_images": 1,
            "max_images": 1,
            "enable_safety_checker": enable_safety_checker
        }
        
        # Combine default negative prompts with any additional ones provided
        combined_negative = self.default_negative_prompt
        if negative_prompt:
            combined_negative = f"{self.default_negative_prompt}, {negative_prompt}" if self.default_negative_prompt else negative_prompt
        if combined_negative:
            payload["negative_prompt"] = combined_negative
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                logger.info(f"Sending request to fal.ai Seedream 4.5 edit endpoint...")
                
                response = await client.post(
                    FAL_EDIT_URL,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    images = result.get("images", [])
                    
                    if images:
                        img_url = images[0].get("url", "")
                        if img_url:
                            img_resp = await client.get(img_url)
                            if img_resp.status_code == 200:
                                save_dir = Path(output_dir) if output_dir else self.output_dir
                                save_dir.mkdir(parents=True, exist_ok=True)
                                
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"{filename_prefix}_{timestamp}.png"
                                filepath = save_dir / filename
                                filepath.write_bytes(img_resp.content)
                                
                                logger.info(f"Image saved: {filepath}")
                                
                                return {
                                    "status": "success",
                                    "image_path": str(filepath),
                                    "filename": filename,
                                    "seed": result.get("seed"),
                                    "provider": "fal.ai",
                                    "model": "seedream-4.5-edit"
                                }
                    
                    return {"status": "error", "error": "No images in response"}
                
                elif response.status_code == 422:
                    error = response.json()
                    logger.warning(f"Content validation error: {error}")
                    return {"status": "error", "error": f"Content blocked: {error}"}
                
                else:
                    logger.error(f"API error {response.status_code}: {response.text[:200]}")
                    return {"status": "error", "error": f"API error: {response.status_code}"}
                    
        except httpx.TimeoutException:
            logger.error("Request timeout")
            return {"status": "error", "error": "Request timeout (>180s)"}
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def generate_from_research_prompt(
        self,
        narrative_prompt: str,
        influencer_id: str = "starbright_monroe",
        aspect_ratio: str = "portrait_4_3"
    ) -> Dict[str, Any]:
        """Generate image from a research-derived narrative prompt"""
        
        full_prompt = self.prompt_builder.build_research_prompt(narrative_prompt)
        
        output_dir = f"content/generated/{influencer_id}"
        
        return await self.generate_with_references(
            prompt=full_prompt,
            aspect_ratio=aspect_ratio,
            output_dir=output_dir,
            filename_prefix=influencer_id,
            enable_safety_checker=False
        )
    
    async def generate_consistency_from_prompt(
        self,
        narrative_prompt: str,
        background: str = "luxury_apartment",
        lighting: str = "soft studio lighting from above",
        aspect_ratio: str = "portrait_4_3"
    ) -> Dict[str, Any]:
        """
        Generate image from a narrative prompt with locked background override.
        
        Takes the full narrative prompt but replaces the setting/background
        with a consistent preset. Uses negative prompts to suppress accessories.
        
        Args:
            narrative_prompt: Full narrative prompt from library
            background: Background preset key (luxury_apartment, studio_white, studio_dark, bedroom)
            lighting: Lighting description
            aspect_ratio: Output aspect ratio
        
        Returns:
            Generation result dict
        """
        full_prompt, negative_prompt = self.prompt_builder.build_consistency_from_narrative(
            narrative_prompt=narrative_prompt,
            background=background,
            lighting=lighting
        )
        
        logger.info(f"Consistency from prompt: background='{background}'")
        logger.info(f"Negative prompt: {negative_prompt}")
        
        return await self.generate_with_references(
            prompt=full_prompt,
            aspect_ratio=aspect_ratio,
            output_dir=str(self.output_dir),
            filename_prefix=f"{self.influencer_id}",
            enable_safety_checker=False,
            negative_prompt=negative_prompt
        )
    
    async def generate_consistency_mode(
        self,
        pose: str,
        outfit: str,
        background: str = "luxury_apartment",
        lighting: str = "soft natural daylight",
        aspect_ratio: str = "portrait_4_3"
    ) -> Dict[str, Any]:
        """
        Generate image in consistency mode with locked background and no accessories.
        
        Args:
            pose: Exact pose description (e.g., "standing with hands on hips")
            outfit: Clothing description
            background: Background preset key or custom description
            lighting: Lighting setup
            aspect_ratio: Output aspect ratio
        
        Returns:
            Generation result dict
        """
        prompt, negative_prompt = self.prompt_builder.build_consistency_prompt(
            pose=pose,
            outfit=outfit,
            background=background,
            lighting=lighting
        )
        
        logger.info(f"Consistency mode: pose='{pose}', background='{background}'")
        logger.info(f"Negative prompt: {negative_prompt}")
        
        return await self.generate_with_references(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            output_dir=str(self.output_dir),
            filename_prefix=f"{self.influencer_id}_consistency",
            enable_safety_checker=False,
            negative_prompt=negative_prompt
        )


    async def transform_with_pose_source(
        self,
        pose_source_path: str,
        pose_description: str,
        outfit_description: str,
        background_description: str = "indoor room",
        background_ref_path: Optional[str] = None,
        aspect_ratio: str = "portrait_4_3",
        output_dir: Optional[str] = None,
        filename_prefix: str = "transformed"
    ) -> Dict[str, Any]:
        """
        Transform a source image to Starbright using the KREATOR FLOW method.
        
        This is the PROVEN WORKING approach for pose/outfit transfer with identity preservation.
        Uses 3-4 references: face (ref1), body (ref2), pose source (ref3), optional background (ref4).
        
        The prompt explicitly states:
        - What to KEEP from the pose source (pose, outfit, camera angle)
        - What to REPLACE with Starbright's identity (face features, body proportions)
        - Optional: What background to use from ref4
        
        Args:
            pose_source_path: Path to the source image to transform
            pose_description: Detailed description of the pose
            outfit_description: Description of the outfit to preserve
            background_description: Description of the background
            background_ref_path: Optional path to background reference image
            aspect_ratio: Output aspect ratio
            output_dir: Optional output directory
            filename_prefix: Prefix for output filename
        
        Returns:
            Generation result dict with image_path
        """
        if not self.fal_key:
            return {"status": "error", "error": "FAL_KEY not configured"}
        
        # Get face and body references
        face_uri, body_uri = self._get_reference_uris("")
        if not face_uri or not body_uri:
            return {"status": "error", "error": "Reference images not found"}
        
        # Encode pose source image
        if not Path(pose_source_path).exists():
            return {"status": "error", "error": f"Pose source not found: {pose_source_path}"}
        
        pose_uri = self._encode_image(pose_source_path)
        
        # KREATOR FLOW PROMPT STRUCTURE - PROVEN WORKING
        # Order: face (ref1), body (ref2), pose (ref3), optional background (ref4)
        image_urls = [face_uri, body_uri, pose_uri]
        
        # Optional background reference as 4th image
        background_prompt_section = ""
        if background_ref_path and Path(background_ref_path).exists():
            bg_uri = self._encode_image(background_ref_path)
            image_urls.append(bg_uri)
            background_prompt_section = f"Use the background/environment from reference4. "
            logger.info(f"Added background reference: {background_ref_path}")
        
        # Get Starbright identity descriptors
        config = INFLUENCER_IDENTITIES.get(self.influencer_id, INFLUENCER_IDENTITIES["starbright_monroe"])
        face_descriptors = config.get("face_descriptors", "hazel-brown eyes, full lips, natural freckles, dark brown hair")
        body_descriptors = config.get("body_descriptors", "slim petite healthy build, natural A-cup")
        
        # Direct subject reference approach - use face/body from references directly
        prompt = f"""Same person from reference1, same body from reference2, in the pose from reference3: {pose_description}.

Subject face from reference1: {face_descriptors}.
Subject body from reference2: {body_descriptors}.

From reference3 ONLY use: pose position, camera angle, {outfit_description} outfit.

{background_prompt_section}{background_description}.

Photorealistic, high detail, sharp focus, 8K quality."""

        negative_prompt = f"Original influencer's face, blue eyes, green eyes, black hair, blonde hair, light hair, different face, wrong identity, large bust, big chest, curvy, busty, {self.default_negative_prompt}"
        
        headers = {
            "Authorization": f"Key {self.fal_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "image_urls": image_urls,
            "image_size": "auto_4K",
            "num_images": 1,
            "enable_safety_checker": False,
            "negative_prompt": negative_prompt,
            "guidance_scale": 5.5,  # 4.5-6.0 for portraits
            "num_inference_steps": 30,
            "seed": 42  # Lock seed for identity consistency
        }
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                logger.info(f"Kreator Flow transform: pose='{pose_description[:50]}...'")
                logger.info(f"Prompt: {prompt[:200]}...")
                
                response = await client.post(FAL_EDIT_URL, headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    images = result.get("images", [])
                    
                    if images:
                        img_url = images[0].get("url", "")
                        if img_url:
                            img_resp = await client.get(img_url)
                            if img_resp.status_code == 200:
                                save_dir = Path(output_dir) if output_dir else self.output_dir
                                save_dir.mkdir(parents=True, exist_ok=True)
                                
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"{filename_prefix}_{timestamp}.png"
                                filepath = save_dir / filename
                                filepath.write_bytes(img_resp.content)
                                
                                logger.info(f"Kreator Flow transform saved: {filepath}")
                                
                                return {
                                    "status": "success",
                                    "image_path": str(filepath),
                                    "filename": filename,
                                    "seed": result.get("seed"),
                                    "provider": "fal.ai",
                                    "model": "seedream-4.5-edit",
                                    "method": "kreator_flow_transform"
                                }
                    
                    return {"status": "error", "error": "No images in response"}
                
                elif response.status_code == 422:
                    error = response.json()
                    logger.warning(f"Content validation error: {error}")
                    return {"status": "error", "error": f"Content blocked: {error}"}
                
                else:
                    logger.error(f"API error {response.status_code}: {response.text[:200]}")
                    return {"status": "error", "error": f"API error: {response.status_code}"}
                    
        except httpx.TimeoutException:
            logger.error("Request timeout")
            return {"status": "error", "error": "Request timeout (>300s)"}
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
            return {"status": "error", "error": str(e)}


fal_seedream_service = FalSeedreamService()
