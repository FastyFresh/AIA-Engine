"""
Wan-2.2 Animate Replace Service - Video Character Replacement

Uses fal.ai's Wan-2.2 model to replace characters in videos while preserving
scene lighting, color tone, and environmental integration.

Pricing:
- $0.08 per video second for 720p
- $0.06 per video second for 580p
- $0.04 per video second for 480p
"""

import os
import asyncio
import httpx
import fal_client
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class WanCharacterReplaceService:
    """Service for replacing characters in videos using Wan-2.2 Animate Replace."""
    
    def __init__(self):
        self.api_key = os.environ.get("FAL_KEY")
        if not self.api_key:
            raise ValueError("FAL_KEY environment variable not set")
        
        self.model_id = "fal-ai/wan/v2.2-14b/animate/replace"
        self.output_dir = Path("content/video_replacements")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def replace_character_sync(
        self,
        video_path: str,
        character_image_path: str,
        resolution: str = "720p",
        guidance_scale: float = 1.0,
        num_inference_steps: int = 20,
        filename_prefix: str = "wan_replace"
    ) -> Dict[str, Any]:
        """
        Replace the character in a video with the character from the image (synchronous).
        
        Args:
            video_path: Path to the source video
            character_image_path: Path to the character image to use as replacement
            resolution: Output resolution - "480p", "580p", or "720p"
            guidance_scale: CFG scale (1-5), higher = better prompt adherence
            num_inference_steps: Sampling steps (1-50), higher = better quality
            filename_prefix: Prefix for the output filename
            
        Returns:
            Dict with status, video_path, and other metadata
        """
        try:
            print(f"Uploading video: {video_path}")
            video_url = fal_client.upload_file(Path(video_path))
            print(f"Video uploaded: {video_url[:80]}...")
            
            print(f"Uploading character image: {character_image_path}")
            image_url = fal_client.upload_file(Path(character_image_path))
            print(f"Image uploaded: {image_url[:80]}...")
            
            print(f"Submitting character replacement request...")
            print(f"  Resolution: {resolution}")
            print(f"  Guidance scale: {guidance_scale}")
            print(f"  Inference steps: {num_inference_steps}")
            
            def on_queue_update(update):
                if isinstance(update, fal_client.Queued):
                    print(f"Queued. Position: {update.position}")
                elif isinstance(update, fal_client.InProgress):
                    if update.logs:
                        for log in update.logs:
                            print(f"  {log.get('message', log) if isinstance(log, dict) else log}")
            
            result = fal_client.subscribe(
                self.model_id,
                arguments={
                    "video_url": video_url,
                    "image_url": image_url,
                    "resolution": resolution,
                    "guidance_scale": guidance_scale,
                    "num_inference_steps": num_inference_steps,
                    "enable_safety_checker": False
                },
                with_logs=True,
                on_queue_update=on_queue_update
            )
            
            video_data = result.get("video", {})
            output_video_url = video_data.get("url")
            
            if not output_video_url:
                return {
                    "status": "error",
                    "error": "No video URL in result",
                    "result": result
                }
            
            print(f"Video generated: {output_video_url[:80]}...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{filename_prefix}_{timestamp}.mp4"
            output_path = self.output_dir / output_filename
            
            with httpx.Client(timeout=120.0) as client:
                response = client.get(output_video_url)
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    print(f"Video saved to: {output_path}")
                else:
                    return {
                        "status": "error",
                        "error": f"Failed to download video: {response.status_code}"
                    }
            
            return {
                "status": "success",
                "video_path": str(output_path),
                "video_url": output_video_url,
                "seed": result.get("seed"),
                "resolution": resolution
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def replace_character(
        self,
        video_path: str,
        character_image_path: str,
        resolution: str = "720p",
        guidance_scale: float = 1.0,
        num_inference_steps: int = 20,
        filename_prefix: str = "wan_replace"
    ) -> Dict[str, Any]:
        """
        Replace the character in a video with the character from the image (async wrapper).
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.replace_character_sync(
                video_path=video_path,
                character_image_path=character_image_path,
                resolution=resolution,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                filename_prefix=filename_prefix
            )
        )


def test_replace():
    """Test the character replacement service."""
    service = WanCharacterReplaceService()
    
    result = service.replace_character_sync(
        video_path="attached_assets/SnapInsta.to_AQPfwrIcwrGYS2Ub1Q4SjN3BgwOdHmzNMetPQGGzBwijXwKYO_1766351887805.mp4",
        character_image_path="content/references/starbright_monroe/starbright_face_no_earrings.png",
        resolution="720p",
        filename_prefix="starbright_yoga_replace"
    )
    
    print(f"\nResult: {result}")
    return result


if __name__ == "__main__":
    test_replace()
