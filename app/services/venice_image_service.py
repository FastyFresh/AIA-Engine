"""
Venice AI Image Generation Service

Privacy-focused, uncensored image generation using Venice AI API.
Supports multiple models including lustify-sdxl for less restrictive content.
"""

import os
import base64
import httpx
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

VENICE_API_BASE = "https://api.venice.ai/api/v1"


class VeniceImageService:
    """Venice AI image generation service with uncensored capabilities"""
    
    def __init__(self):
        self.api_key = os.environ.get("VENICE_API_KEY")
        self.output_dir = "content/venice_output"
        self.default_model = "fluently-xl"
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        cfg_scale: float = 7.5,
        seed: Optional[int] = None,
        style_preset: Optional[str] = None,
        variants: int = 1,
        filename_prefix: str = "venice",
        hide_watermark: bool = True
    ) -> Dict[str, Any]:
        """
        Generate image using Venice AI
        
        Args:
            prompt: Text description of desired image
            model: Model to use (fluently-xl, lustify-sdxl, nano-banana-pro, z-image-turbo)
            negative_prompt: What should NOT appear
            width: Image width in pixels
            height: Image height in pixels
            cfg_scale: Classifier-free guidance scale
            seed: Random seed for reproducibility
            style_preset: Style preset (Photographic, Anime, etc.)
            variants: Number of images (1-4)
            filename_prefix: Prefix for saved filename
            hide_watermark: Remove Venice watermark
            
        Returns:
            Dict with status, image_path(s), and metadata
        """
        
        if not self.api_key:
            return {"status": "error", "error": "VENICE_API_KEY not configured"}
        
        model = model or self.default_model
        
        input_data = {
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "cfg_scale": cfg_scale,
            "variants": variants,
            "format": "png",
            "hide_watermark": hide_watermark,
            "return_binary": False
        }
        
        if negative_prompt:
            input_data["negative_prompt"] = negative_prompt
        if seed is not None:
            input_data["seed"] = seed
        if style_preset:
            input_data["style_preset"] = style_preset
        
        try:
            logger.info(f"Venice AI generation: {model}, {width}x{height}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{VENICE_API_BASE}/image/generate",
                    headers=self.get_headers(),
                    json=input_data
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Venice API error: {error_text}")
                    return {"status": "error", "error": f"API error: {error_text}"}
                
                result = response.json()
                
                images = result.get("images", [])
                if not images:
                    return {"status": "error", "error": "No images returned"}
                
                saved_paths = []
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                for idx, img_b64 in enumerate(images):
                    img_data = base64.b64decode(img_b64)
                    
                    if len(images) > 1:
                        filename = f"{filename_prefix}_{timestamp}_{idx+1}.png"
                    else:
                        filename = f"{filename_prefix}_{timestamp}.png"
                    
                    filepath = os.path.join(self.output_dir, filename)
                    
                    with open(filepath, "wb") as f:
                        f.write(img_data)
                    
                    saved_paths.append(filepath)
                    logger.info(f"Saved Venice image: {filepath}")
                
                if len(saved_paths) == 1:
                    return {
                        "status": "success",
                        "image_path": saved_paths[0],
                        "filename": os.path.basename(saved_paths[0]),
                        "prompt": prompt,
                        "model": model,
                        "provider": "venice"
                    }
                else:
                    return {
                        "status": "success",
                        "image_paths": saved_paths,
                        "filenames": [os.path.basename(p) for p in saved_paths],
                        "prompt": prompt,
                        "model": model,
                        "provider": "venice",
                        "count": len(saved_paths)
                    }
                    
        except httpx.TimeoutException:
            return {"status": "error", "error": "Request timed out"}
        except Exception as e:
            logger.error(f"Venice generation error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def generate_starbright(
        self,
        outfit: str,
        scene: str,
        pose: str = "standing casually",
        model: str = "fluently-xl",
        width: int = 1024,
        height: int = 1360,
        seed: Optional[int] = None,
        filename_prefix: str = "starbright_venice"
    ) -> Dict[str, Any]:
        """
        Generate Starbright Monroe image with Venice AI
        
        Uses Starbright's consistent identity descriptors.
        """
        
        prompt = f"""Portrait, young woman {pose}, wearing {outfit}, {scene}, 
very pale porcelain ivory white skin, straight sleek dark brown hair (not wavy, not curly), 
warm olive-brown eyes, natural freckles across nose and cheeks, 
extremely thin slender petite body with very narrow tiny waist, slim narrow hips, 
long thin slender legs, delicate small frame, 
Shot on Canon EOS R5, 85mm f/1.4 lens, natural skin texture with visible pores, 
8K ultra detailed, professional photography"""
        
        negative_prompt = "tan skin, tanned, blonde hair, curly hair, wavy hair, muscular, thick, heavy"
        
        return await self.generate(
            prompt=prompt,
            model=model,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            seed=seed,
            filename_prefix=filename_prefix,
            style_preset="Photographic"
        )
    
    async def list_models(self) -> Dict[str, Any]:
        """Get available Venice image models"""
        
        if not self.api_key:
            return {"status": "error", "error": "VENICE_API_KEY not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{VENICE_API_BASE}/models",
                    headers=self.get_headers()
                )
                
                if response.status_code != 200:
                    return {"status": "error", "error": response.text}
                
                models = response.json()
                image_models = [m for m in models.get("data", []) if m.get("type") == "image"]
                
                return {
                    "status": "success",
                    "models": image_models
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def list_styles(self) -> Dict[str, Any]:
        """Get available style presets"""
        
        if not self.api_key:
            return {"status": "error", "error": "VENICE_API_KEY not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{VENICE_API_BASE}/image/styles",
                    headers=self.get_headers()
                )
                
                if response.status_code != 200:
                    return {"status": "error", "error": response.text}
                
                return {
                    "status": "success",
                    "styles": response.json()
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}


venice_image_service = VeniceImageService()
