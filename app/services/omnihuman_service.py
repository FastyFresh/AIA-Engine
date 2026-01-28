"""
OmniHuman v1.5 Video Generation Service - Lip-Sync Avatar Videos

Uses fal.ai's ByteDance OmniHuman v1.5 for generating talking avatar videos
from a single image + audio file. Excellent for DFans lip-sync content.

Features:
- Single image input (uses Starbright hero images)
- Audio-driven animation with lip-sync
- Up to 60 seconds at 720p
- Turbo mode for faster iteration
- Auto-resize images >5MB for API compliance
"""

import os
import fal_client
import logging
import httpx
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

OMNIHUMAN_ENDPOINT = "fal-ai/bytedance/omnihuman/v1.5"
MAX_IMAGE_SIZE = 5 * 1024 * 1024


class OmniHumanService:
    """
    Video generation service using OmniHuman v1.5 for lip-sync talking videos.
    
    Converts hero images into talking avatar videos driven by audio.
    Perfect for DFans funnel content with personalized messages.
    """
    
    def __init__(self):
        self.fal_key = os.getenv("FAL_KEY", "")
        self.output_dir = Path("content/videos/omnihuman")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("/tmp/omnihuman_temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info("OmniHuman v1.5 Service initialized")
    
    def _resize_image_if_needed(self, image_path: str) -> str:
        """Resize image if it exceeds 5MB limit"""
        file_size = Path(image_path).stat().st_size
        
        if file_size <= MAX_IMAGE_SIZE:
            return image_path
        
        logger.info(f"Image {file_size/1024/1024:.1f}MB exceeds 5MB limit, resizing...")
        
        resized_path = self.temp_dir / f"resized_{Path(image_path).stem}.jpg"
        
        subprocess.run([
            "magick", image_path,
            "-resize", "1280x1280>",
            "-quality", "85",
            str(resized_path)
        ], check=True, capture_output=True)
        
        new_size = resized_path.stat().st_size
        logger.info(f"Resized to {new_size/1024:.1f}KB")
        
        return str(resized_path)
    
    async def generate_talking_video(
        self,
        image_path: str,
        audio_path: str,
        resolution: str = "720p",
        turbo_mode: bool = False,
        output_dir: Optional[str] = None,
        filename_prefix: str = "omnihuman"
    ) -> Dict[str, Any]:
        """
        Generate a lip-sync talking video from image + audio.
        
        Args:
            image_path: Path to the portrait/hero image (auto-resized if >5MB)
            audio_path: Path to the audio file (mp3, wav, ogg, m4a, aac) - max 60s at 720p
            resolution: "720p" (recommended) or "1080p"
            turbo_mode: Enable faster generation for testing
            output_dir: Custom output directory
            filename_prefix: Prefix for output filename
            
        Returns:
            Dict with status, video_path, duration, and metadata
        """
        
        if not self.fal_key:
            return {"status": "error", "error": "FAL_KEY not configured"}
        
        if not Path(image_path).exists():
            return {"status": "error", "error": f"Image not found: {image_path}"}
        
        if not Path(audio_path).exists():
            return {"status": "error", "error": f"Audio not found: {audio_path}"}
        
        try:
            processed_image = self._resize_image_if_needed(image_path)
            
            logger.info(f"Uploading files to fal storage...")
            image_url = fal_client.upload_file(processed_image)
            audio_url = fal_client.upload_file(audio_path)
            
            logger.info(f"Submitting to OmniHuman v1.5...")
            logger.info(f"Image: {Path(image_path).name}")
            logger.info(f"Audio: {Path(audio_path).name}")
            logger.info(f"Resolution: {resolution}, Turbo: {turbo_mode}")
            
            handle = fal_client.submit(
                OMNIHUMAN_ENDPOINT,
                arguments={
                    "image_url": image_url,
                    "audio_url": audio_url,
                    "resolution": resolution,
                    "turbo_mode": turbo_mode
                }
            )
            
            request_id = handle.request_id
            logger.info(f"Request submitted: {request_id}")
            
            for i in range(120):
                status = fal_client.status(OMNIHUMAN_ENDPOINT, request_id, with_logs=True)
                status_type = type(status).__name__
                
                if status_type == "Completed":
                    result = fal_client.result(OMNIHUMAN_ENDPOINT, request_id)
                    break
                elif status_type == "Failed":
                    return {"status": "error", "error": "Generation failed"}
                
                time.sleep(5)
            else:
                return {"status": "error", "error": "Generation timed out (10 min)"}
            
            logger.info(f"OmniHuman complete. Result keys: {list(result.keys())}")
            
            video_data = result.get("video", {})
            video_url = video_data.get("url")
            duration = result.get("duration", 0)
            
            if not video_url:
                return {"status": "error", "error": "No video URL in response"}
            
            save_dir = Path(output_dir) if output_dir else self.output_dir
            save_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.mp4"
            filepath = save_dir / filename
            
            video_resp = httpx.get(video_url, timeout=180.0)
            if video_resp.status_code == 200:
                filepath.write_bytes(video_resp.content)
                logger.info(f"Video saved: {filepath} ({duration:.1f}s)")
            else:
                return {"status": "error", "error": f"Download failed: {video_resp.status_code}"}
            
            estimated_cost = duration * 0.16
            
            return {
                "status": "success",
                "video_path": str(filepath),
                "filename": filename,
                "video_url": video_url,
                "duration": duration,
                "estimated_cost": f"${estimated_cost:.2f}",
                "provider": "fal.ai",
                "model": "omnihuman-v1.5"
            }
            
        except Exception as e:
            logger.error(f"OmniHuman generation error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def generate_flirty_message(
        self,
        image_path: str,
        audio_path: str,
        turbo_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a flirty talking video for DFans funnel.
        Optimized settings for personal message style content.
        
        Args:
            image_path: Path to Starbright hero image
            audio_path: Path to audio message (keep under 30s for best quality)
            turbo_mode: Enable for faster testing
        """
        return await self.generate_talking_video(
            image_path=image_path,
            audio_path=audio_path,
            resolution="720p",
            turbo_mode=turbo_mode,
            filename_prefix="starbright_message"
        )


omnihuman_service = OmniHumanService()
