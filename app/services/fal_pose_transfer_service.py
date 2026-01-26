"""
Fal.ai Pose Transfer Service - Character Transfer with Pose Preservation

Uses Leffa Pose Transfer endpoint to:
1. Extract exact pose from source image
2. Apply Starbright's identity via person_image conditioning
3. Generate new image with preserved pose and new identity
"""

import os
import asyncio
import fal_client
import logging
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

GENERATION_TIMEOUT = 300  # 5 minutes timeout for generation


class FalPoseTransferService:
    """
    Character transfer service that preserves pose while applying new identity.
    Uses Leffa Pose Transfer endpoint (fal-ai/leffa/pose-transfer).
    
    Workflow:
    1. Upload pose image (influencer with desired pose)
    2. Upload person image (Starbright reference for identity)
    3. Generate with pose from first, identity from second
    """
    
    def __init__(self):
        self.fal_key = os.getenv("FAL_KEY", "")
        self.output_dir = Path("content/generated/pose_transfer")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.starbright_face_ref = "content/references/starbright_monroe/starbright_face_reference_v2.png"
        
        logger.info("Fal.ai Pose Transfer Service initialized (Leffa endpoint)")
    
    def _upload_to_fal(self, file_path: str) -> Optional[str]:
        """Upload a local file to Fal.ai storage and return the URL."""
        try:
            url = fal_client.upload_file(file_path)
            logger.info(f"Uploaded to Fal: {url}")
            return url
        except Exception as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            return None
    
    def _is_url(self, path: str) -> bool:
        return path.startswith("http://") or path.startswith("https://")
    
    def _get_starbright_face_path(self) -> Optional[str]:
        ref_path = Path(self.starbright_face_ref)
        if ref_path.exists():
            return str(ref_path.absolute())
        
        alt_paths = [
            "content/references/starbright_monroe/canonical_face/face_01.png",
            "content/references/starbright_monroe/starbright_001.webp"
        ]
        for alt in alt_paths:
            if Path(alt).exists():
                return str(Path(alt).absolute())
        return None
    
    async def transfer_pose(
        self,
        pose_image_url: str,
        person_image_url: Optional[str] = None,
        num_inference_steps: int = 50,
        guidance_scale: float = 2.5,
        seed: Optional[int] = None,
        output_dir: Optional[str] = None,
        filename_prefix: str = "pose_transfer"
    ) -> Dict[str, Any]:
        """
        Transfer pose from source image to Starbright's identity.
        
        Args:
            pose_image_url: URL/path of source image with desired pose
            person_image_url: Starbright's reference (auto-detected if None)
            num_inference_steps: Number of inference steps (default: 50)
            guidance_scale: CFG scale (default: 2.5)
            seed: Random seed for reproducibility
        """
        if not self.fal_key:
            return {"status": "error", "error": "FAL_KEY not configured"}
        
        active_person_ref = person_image_url
        if not active_person_ref:
            local_face_path = self._get_starbright_face_path()
            if local_face_path and Path(local_face_path).exists():
                active_person_ref = self._upload_to_fal(local_face_path)
            else:
                return {"status": "error", "error": "No person reference available"}
        elif not self._is_url(active_person_ref) and Path(active_person_ref).exists():
            active_person_ref = self._upload_to_fal(active_person_ref)
        
        if not active_person_ref:
            return {"status": "error", "error": "Failed to upload person reference"}
        
        if not self._is_url(pose_image_url) and Path(pose_image_url).exists():
            pose_image_url = self._upload_to_fal(pose_image_url)
            if not pose_image_url:
                return {"status": "error", "error": "Failed to upload pose image"}
        
        arguments = {
            "pose_image_url": pose_image_url,
            "person_image_url": active_person_ref,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "enable_safety_checker": False,
            "output_format": "png"
        }
        
        if seed is not None:
            arguments["seed"] = seed
        
        logger.info(f"Transferring pose from: {pose_image_url[:50]}...")
        logger.info(f"Person image: {active_person_ref[:50]}...")
        logger.info(f"Settings: steps={num_inference_steps}, guidance={guidance_scale}")
        
        try:
            result = await asyncio.wait_for(
                fal_client.subscribe_async(
                    "fal-ai/leffa/pose-transfer",
                    arguments=arguments,
                    with_logs=True,
                    on_queue_update=lambda update: logger.info(f"Queue update: {update}")
                ),
                timeout=GENERATION_TIMEOUT
            )
            
            image = result.get("image", {})
            img_url = image.get("url", "")
            
            if img_url:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    img_resp = await client.get(img_url)
                    if img_resp.status_code == 200:
                        save_dir = Path(output_dir) if output_dir else self.output_dir
                        save_dir.mkdir(parents=True, exist_ok=True)
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{filename_prefix}_{timestamp}.png"
                        filepath = save_dir / filename
                        filepath.write_bytes(img_resp.content)
                        logger.info(f"Saved: {filepath}")
                        
                        return {
                            "status": "success",
                            "image": str(filepath),
                            "seed": result.get("seed"),
                            "provider": "fal.ai",
                            "model": "leffa-pose-transfer"
                        }
            
            return {"status": "error", "error": "No image in response", "raw": result}
        
        except asyncio.TimeoutError:
            logger.error(f"Generation timed out after {GENERATION_TIMEOUT}s")
            return {"status": "error", "error": f"Generation timed out after {GENERATION_TIMEOUT} seconds"}
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Exception: {error_msg}")
            if "detail" in error_msg.lower():
                return {"status": "error", "error": f"API validation error: {error_msg}"}
            return {"status": "error", "error": error_msg}
    
    async def batch_transfer(
        self,
        pose_images: List[str],
        person_image_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Batch process multiple images with pose transfer."""
        results = {
            "status": "success",
            "processed": 0,
            "failed": 0,
            "images": [],
            "errors": []
        }
        
        person_url = person_image_url
        if not person_url:
            local_path = self._get_starbright_face_path()
            if local_path:
                person_url = self._upload_to_fal(local_path)
        
        for i, pose_img in enumerate(pose_images):
            logger.info(f"Processing image {i+1}/{len(pose_images)}")
            
            result = await self.transfer_pose(
                pose_image_url=pose_img,
                person_image_url=person_url,
                filename_prefix=f"batch_{i+1:03d}",
                **kwargs
            )
            
            if result.get("status") == "success":
                results["processed"] += 1
                results["images"].append(result.get("image"))
            else:
                results["failed"] += 1
                results["errors"].append({
                    "source": pose_img,
                    "error": result.get("error")
                })
        
        if results["failed"] > 0 and results["processed"] == 0:
            results["status"] = "error"
        elif results["failed"] > 0:
            results["status"] = "partial"
        
        return results
    
    async def upload_and_transfer(
        self,
        pose_image_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Upload a local pose image and perform pose transfer."""
        pose_url = self._upload_to_fal(pose_image_path)
        if not pose_url:
            return {"status": "error", "error": f"Failed to upload {pose_image_path}"}
        
        return await self.transfer_pose(pose_image_url=pose_url, **kwargs)


fal_pose_transfer_service = FalPoseTransferService()
