"""
OmniHuman v1.5 Video Generation Service - Lip-Sync Avatar Videos

Uses fal.ai's ByteDance OmniHuman v1.5 for generating talking avatar videos
from a single image + audio file. Excellent for DFans lip-sync content.

Features:
- Single image input (uses Starbright hero images)
- Audio-driven animation with lip-sync
- Up to 60 seconds at 720p
- Turbo mode for faster iteration
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

OMNIHUMAN_ENDPOINT = "fal-ai/bytedance/omnihuman/v1.5"


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
        logger.info("OmniHuman v1.5 Service initialized")
    
    def _encode_to_data_uri(self, file_path: str) -> str:
        """Encode local file to data URI"""
        with open(file_path, "rb") as f:
            file_data = base64.b64encode(f.read()).decode()
        
        ext = Path(file_path).suffix.lower()
        
        image_mimes = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp"
        }
        
        audio_mimes = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
            ".aac": "audio/aac"
        }
        
        mime = image_mimes.get(ext) or audio_mimes.get(ext, "application/octet-stream")
        
        return f"data:{mime};base64,{file_data}"
    
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
            image_path: Path to the portrait/hero image
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
        
        image_url = self._encode_to_data_uri(image_path)
        audio_url = self._encode_to_data_uri(audio_path)
        
        try:
            logger.info(f"Submitting to OmniHuman v1.5...")
            logger.info(f"Image: {Path(image_path).name}")
            logger.info(f"Audio: {Path(audio_path).name}")
            logger.info(f"Resolution: {resolution}, Turbo: {turbo_mode}")
            
            def on_queue_update(update):
                if isinstance(update, fal_client.InProgress):
                    logger.info(f"OmniHuman generation in progress...")
                    for log in update.logs:
                        logger.info(f"  {log.get('message', '')}")
            
            result = fal_client.subscribe(
                OMNIHUMAN_ENDPOINT,
                arguments={
                    "image_url": image_url,
                    "audio_url": audio_url,
                    "resolution": resolution,
                    "turbo_mode": turbo_mode
                },
                with_logs=True,
                on_queue_update=on_queue_update
            )
            
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
            
            async with httpx.AsyncClient(timeout=180.0) as client:
                video_resp = await client.get(video_url)
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
