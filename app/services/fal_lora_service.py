"""
Fal.ai LoRA Service - Custom LoRA Image Generation

Supports uploading and using custom safetensor LoRA models with Fal.ai's Flux-LoRA endpoint.
Use this service when you have a trained LoRA model (safetensor) that you want to use for generation.
"""

import os
import httpx
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

FAL_FLUX_LORA_URL = "https://fal.run/fal-ai/flux-lora"
FAL_SDXL_LORA_URL = "https://fal.run/fal-ai/lora"


class FalLoraService:
    """
    Service for generating images using custom LoRA models with Fal.ai's Flux-LoRA endpoint.
    
    Workflow:
    1. Upload safetensor LoRA to Fal.ai storage
    2. Generate images using the uploaded LoRA with custom prompts
    """
    
    def __init__(self, lora_path: Optional[str] = None):
        self.fal_key = os.getenv("FAL_KEY", "")
        self.lora_path = lora_path
        self.lora_url = None
        self.output_dir = Path("content/generated/lora")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Fal.ai LoRA Service initialized")
    
    async def upload_lora(self, lora_path: str) -> Dict[str, Any]:
        """
        Upload a safetensor LoRA file to Fal.ai storage using the official client.
        Returns the URL to use for generation.
        """
        if not self.fal_key:
            return {"status": "error", "error": "FAL_KEY not configured"}
        
        lora_file = Path(lora_path)
        if not lora_file.exists():
            return {"status": "error", "error": f"LoRA file not found: {lora_path}"}
        
        file_size = lora_file.stat().st_size
        logger.info(f"Uploading LoRA: {lora_file.name} ({file_size / 1024 / 1024:.1f} MB)")
        
        try:
            import fal_client
            
            lora_url = fal_client.upload_file(lora_path)
            self.lora_url = lora_url
            logger.info(f"LoRA uploaded successfully: {self.lora_url}")
            return {
                "status": "success",
                "lora_url": self.lora_url,
                "file_name": lora_file.name
            }
                    
        except Exception as e:
            logger.error(f"Upload exception: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def generate_with_lora(
        self,
        prompt: str,
        lora_url: Optional[str] = None,
        lora_scale: float = 1.0,
        image_size: str = "portrait_4_3",
        num_inference_steps: int = 28,
        guidance_scale: float = 3.5,
        num_images: int = 1,
        output_dir: Optional[str] = None,
        filename_prefix: str = "lora_gen"
    ) -> Dict[str, Any]:
        """
        Generate image(s) using a custom LoRA with Fal.ai Flux-LoRA.
        
        Args:
            prompt: Text prompt for generation
            lora_url: URL to the LoRA safetensor (use uploaded URL or provide new one)
            lora_scale: LoRA influence strength (0.0 to 2.0, default 1.0)
            image_size: Output size (portrait_4_3, landscape_4_3, square, etc.)
            num_inference_steps: Number of diffusion steps (default 28)
            guidance_scale: CFG scale (default 3.5)
            num_images: Number of images to generate
            output_dir: Custom output directory
            filename_prefix: Prefix for saved files
        """
        if not self.fal_key:
            return {"status": "error", "error": "FAL_KEY not configured"}
        
        active_lora_url = lora_url or self.lora_url
        if not active_lora_url:
            return {"status": "error", "error": "No LoRA URL provided. Upload a LoRA first."}
        
        headers = {
            "Authorization": f"Key {self.fal_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "loras": [
                {
                    "path": active_lora_url,
                    "scale": lora_scale
                }
            ],
            "image_size": image_size,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "num_images": num_images,
            "enable_safety_checker": False,
            "output_format": "png"
        }
        
        logger.info(f"Generating with LoRA (scale={lora_scale}): {prompt[:100]}...")
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    FAL_FLUX_LORA_URL,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    images = result.get("images", [])
                    
                    if images:
                        saved_paths = []
                        save_dir = Path(output_dir) if output_dir else self.output_dir
                        save_dir.mkdir(parents=True, exist_ok=True)
                        
                        for i, img_data in enumerate(images):
                            img_url = img_data.get("url", "")
                            if img_url:
                                img_resp = await client.get(img_url)
                                if img_resp.status_code == 200:
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    suffix = f"_{i+1}" if num_images > 1 else ""
                                    filename = f"{filename_prefix}_{timestamp}{suffix}.png"
                                    filepath = save_dir / filename
                                    filepath.write_bytes(img_resp.content)
                                    saved_paths.append(str(filepath))
                                    logger.info(f"Saved: {filepath}")
                        
                        return {
                            "status": "success",
                            "images": saved_paths,
                            "seed": result.get("seed"),
                            "provider": "fal.ai",
                            "model": "flux-lora",
                            "lora_scale": lora_scale
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
    
    async def generate_with_sdxl_lora(
        self,
        prompt: str,
        lora_url: Optional[str] = None,
        lora_scale: float = 1.0,
        negative_prompt: str = "blurry, low quality, distorted, deformed",
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        num_images: int = 1,
        image_size: Dict[str, int] = None,
        output_dir: Optional[str] = None,
        filename_prefix: str = "sdxl_lora"
    ) -> Dict[str, Any]:
        """
        Generate image(s) using a custom LoRA with Fal.ai SDXL LoRA endpoint.
        This is better for LoRAs trained on SDXL architecture.
        
        Args:
            prompt: Text prompt for generation
            lora_url: URL to the LoRA safetensor
            lora_scale: LoRA influence strength (0.0 to 2.0, default 1.0)
            negative_prompt: What to avoid in the image
            num_inference_steps: Number of diffusion steps (default 30)
            guidance_scale: CFG scale (default 7.5 for SDXL)
            num_images: Number of images to generate
            image_size: Dict with width/height (default 768x1024 for portrait)
            output_dir: Custom output directory
            filename_prefix: Prefix for saved files
        """
        if not self.fal_key:
            return {"status": "error", "error": "FAL_KEY not configured"}
        
        active_lora_url = lora_url or self.lora_url
        if not active_lora_url:
            return {"status": "error", "error": "No LoRA URL provided. Upload a LoRA first."}
        
        if image_size is None:
            image_size = {"width": 768, "height": 1024}
        
        headers = {
            "Authorization": f"Key {self.fal_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model_name": "stabilityai/stable-diffusion-xl-base-1.0",
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "loras": [
                {
                    "path": active_lora_url,
                    "scale": lora_scale
                }
            ],
            "image_size": image_size,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "num_images": num_images,
            "enable_safety_checker": False,
            "output_format": "png"
        }
        
        logger.info(f"Generating with SDXL LoRA (scale={lora_scale}): {prompt[:100]}...")
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    FAL_SDXL_LORA_URL,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    images = result.get("images", [])
                    
                    if images:
                        saved_paths = []
                        save_dir = Path(output_dir) if output_dir else self.output_dir
                        save_dir.mkdir(parents=True, exist_ok=True)
                        
                        for i, img_data in enumerate(images):
                            img_url = img_data.get("url", "")
                            if img_url:
                                img_resp = await client.get(img_url)
                                if img_resp.status_code == 200:
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    suffix = f"_{i+1}" if num_images > 1 else ""
                                    filename = f"{filename_prefix}_{timestamp}{suffix}.png"
                                    filepath = save_dir / filename
                                    filepath.write_bytes(img_resp.content)
                                    saved_paths.append(str(filepath))
                                    logger.info(f"Saved: {filepath}")
                        
                        return {
                            "status": "success",
                            "images": saved_paths,
                            "seed": result.get("seed"),
                            "provider": "fal.ai",
                            "model": "sdxl-lora",
                            "lora_scale": lora_scale
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
    
    async def generate_starbright(
        self,
        scene: str,
        outfit: str = "elegant white sundress",
        pose: str = "standing confidently",
        lighting: str = "soft natural lighting",
        lora_scale: float = 1.2,
        aspect_ratio: str = "portrait_4_3"
    ) -> Dict[str, Any]:
        """
        Generate a Starbright image using the custom LoRA with identity-preserving prompt.
        
        Uses "Starbright18" as the trigger word for best identity consistency.
        """
        full_prompt = (
            f"Starbright18, {pose}, wearing {outfit}, {scene}, {lighting}, "
            "professional photography, Canon EOS R5, 85mm f/1.4 lens, "
            "natural skin texture, 8K quality"
        )
        
        return await self.generate_with_lora(
            prompt=full_prompt,
            lora_scale=lora_scale,
            image_size=aspect_ratio,
            filename_prefix="starbright_lora"
        )


fal_lora_service = FalLoraService()
