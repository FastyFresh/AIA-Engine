"""
Fal.ai Video Generation Service - Reel/Short-Form Video Generation

Uses fal.ai's Kling video models for image-to-video generation.
Supports multiple Kling versions for different quality/speed tradeoffs.

Available Models:
- Kling v2.1 Pro: Good quality, faster
- Kling v2.1 Master: Highest quality, slower
"""

import os
import fal_client
import logging
import base64
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

KLING_PRO = "fal-ai/kling-video/v2.1/pro/image-to-video"
KLING_MASTER = "fal-ai/kling-video/v2.1/master/image-to-video"


class FalVideoService:
    """
    Video generation service using fal.ai Kling models.
    
    Converts hero images into short-form videos (reels) with
    subtle motion and cinematic quality.
    """
    
    def __init__(self):
        self.fal_key = os.getenv("FAL_KEY", "")
        self.output_dir = Path("content/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Fal.ai Video Service initialized")
    
    def _encode_image_to_data_uri(self, image_path: str) -> str:
        """Encode local image to data URI"""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        ext = Path(image_path).suffix.lower()
        mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp"
        }.get(ext, "image/png")
        
        return f"data:{mime};base64,{image_data}"
    
    async def generate_reel(
        self,
        image_path: str,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        model: str = "pro",
        output_dir: Optional[str] = None,
        filename_prefix: str = "reel"
    ) -> Dict[str, Any]:
        """
        Generate a video reel from a hero image.
        
        Args:
            image_path: Path to the input hero image
            prompt: Motion/action description for the video
            duration: Video duration in seconds (5 or 10)
            aspect_ratio: Output aspect ratio ("9:16" for reels, "16:9" for landscape)
            model: "pro" (faster) or "master" (highest quality)
            output_dir: Custom output directory
            filename_prefix: Prefix for output filename
            
        Returns:
            Dict with status, video_path, and metadata
        """
        
        if not self.fal_key:
            return {"status": "error", "error": "FAL_KEY not configured"}
        
        if not Path(image_path).exists():
            return {"status": "error", "error": f"Image not found: {image_path}"}
        
        endpoint = KLING_MASTER if model == "master" else KLING_PRO
        
        image_url = self._encode_image_to_data_uri(image_path)
        
        try:
            logger.info(f"Submitting video generation to Kling {model}...")
            logger.info(f"Prompt: {prompt[:100]}...")
            logger.info(f"Duration: {duration}s, Aspect: {aspect_ratio}")
            
            def on_queue_update(update):
                if isinstance(update, fal_client.InProgress):
                    logger.info(f"Generation in progress...")
                    for log in update.logs:
                        logger.info(f"  {log.get('message', '')}")
            
            result = fal_client.subscribe(
                endpoint,
                arguments={
                    "prompt": prompt,
                    "image_url": image_url,
                    "duration": str(duration),
                    "aspect_ratio": aspect_ratio
                },
                with_logs=True,
                on_queue_update=on_queue_update
            )
            
            logger.info(f"Generation complete. Result: {list(result.keys())}")
            
            video_data = result.get("video", {})
            video_url = video_data.get("url")
            
            if not video_url:
                return {"status": "error", "error": "No video URL in response"}
            
            save_dir = Path(output_dir) if output_dir else self.output_dir
            save_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.mp4"
            filepath = save_dir / filename
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                video_resp = await client.get(video_url)
                if video_resp.status_code == 200:
                    filepath.write_bytes(video_resp.content)
                    logger.info(f"Video saved: {filepath}")
                else:
                    return {"status": "error", "error": f"Download failed: {video_resp.status_code}"}
            
            return {
                "status": "success",
                "video_path": str(filepath),
                "filename": filename,
                "video_url": video_url,
                "provider": "fal.ai",
                "model": f"kling-v2.1-{model}"
            }
            
        except Exception as e:
            logger.error(f"Video generation error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def generate_viral_reel(
        self,
        image_path: str,
        vibe: str = "alluring_real",
        duration: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a viral reel with pre-built prompts optimized for engagement.
        
        Args:
            image_path: Path to hero image
            vibe: Preset vibe ("alluring_real", "confident", "playful", "mysterious")
            duration: Video length in seconds
            
        Returns:
            Dict with video generation result
        """
        
        prompts = {
            "alluring_real": (
                "Subtle natural movement, she gently shifts her weight and her hair "
                "flows softly in a light breeze, maintaining eye contact with camera, "
                "warm golden hour lighting enhances her features, natural smile appears "
                "briefly, realistic skin texture and movement, cinematic quality, "
                "intimate girlfriend POV feeling"
            ),
            "confident": (
                "She stands confidently with subtle body sway, hair gently moving, "
                "direct eye contact with a knowing smile, smooth natural movement, "
                "professional model energy, cinematic lighting"
            ),
            "playful": (
                "Playful energy with subtle head tilt, gentle laugh, hair flip, "
                "natural joyful expression, warm inviting atmosphere, "
                "candid moment captured, lifestyle photography feel"
            ),
            "mysterious": (
                "Subtle enigmatic expression, slow deliberate movement, "
                "dramatic lighting shifts, she looks away then back to camera, "
                "moody atmospheric, fashion editorial quality"
            )
        }
        
        prompt = prompts.get(vibe, prompts["alluring_real"])
        
        return await self.generate_reel(
            image_path=image_path,
            prompt=prompt,
            duration=duration,
            aspect_ratio="9:16",
            model="master",
            filename_prefix=f"viral_{vibe}"
        )


fal_video_service = FalVideoService()
