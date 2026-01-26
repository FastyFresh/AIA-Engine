"""
Fal.ai InstantID Service - Identity Transfer

Transfers Starbright's identity onto influencer images using InstantID.
This is better than face-swapping as it regenerates the entire image coherently.
"""

import os
import httpx
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

FAL_INSTANTID_URL = "https://fal.run/fal-ai/instantid/lcm"
FAL_IP_ADAPTER_FACE_URL = "https://fal.run/fal-ai/ip-adapter-face-id"


class FalInstantIDService:
    """
    Service for identity transfer using Fal.ai InstantID.
    
    Workflow:
    1. Provide Starbright's face reference image
    2. Provide source image (influencer pose to replicate)
    3. Generate new image with Starbright's identity in that pose
    """
    
    def __init__(self):
        self.fal_key = os.getenv("FAL_KEY", "")
        self.output_dir = Path("content/generated/identity_transfer")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.starbright_face_ref = "content/references/starbright_monroe/body_reference_canonical.png"
        
        logger.info("Fal.ai InstantID Service initialized")
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Key {self.fal_key}",
            "Content-Type": "application/json"
        }
    
    def _upload_to_fal(self, file_path: str) -> Optional[str]:
        """Upload a local file to Fal.ai storage and return the URL."""
        try:
            import fal_client
            url = fal_client.upload_file(file_path)
            logger.info(f"Uploaded to Fal: {url}")
            return url
        except Exception as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            return None
    
    def _is_url(self, path: str) -> bool:
        """Check if a path is a URL."""
        return path.startswith("http://") or path.startswith("https://")
    
    async def transfer_identity(
        self,
        source_image_url: str,
        face_reference_url: Optional[str] = None,
        prompt: str = "professional photography, natural lighting, 8K quality",
        negative_prompt: str = "nsfw, lowres, bad anatomy, bad hands, blurry, deformed",
        ip_adapter_scale: float = 0.8,
        controlnet_conditioning_scale: float = 0.4,
        identity_controlnet_conditioning_scale: float = 0.8,
        num_inference_steps: int = 8,
        guidance_scale: float = 1.5,
        enhance_face_region: bool = True,
        output_dir: Optional[str] = None,
        filename_prefix: str = "identity_transfer"
    ) -> Dict[str, Any]:
        """
        Transfer Starbright's identity onto a source image.
        
        Args:
            source_image_url: URL or path to the source image (pose reference)
            face_reference_url: URL to face reference (defaults to Starbright canonical)
            prompt: Additional prompt for styling
            negative_prompt: What to avoid
            ip_adapter_scale: Face identity strength (0.0-1.0, higher = more like reference)
            controlnet_conditioning_scale: Structural control (0.0-1.0)
            identity_controlnet_conditioning_scale: Facial landmark control
            num_inference_steps: Quality steps (5-20, higher = better but slower)
            guidance_scale: Prompt adherence
            enhance_face_region: Additional face enhancement
            output_dir: Custom output directory
            filename_prefix: Prefix for saved files
        """
        if not self.fal_key:
            return {"status": "error", "error": "FAL_KEY not configured"}
        
        # Get face reference - upload to Fal if it's a local path
        active_face_ref = face_reference_url
        if not active_face_ref:
            local_face_path = self._get_starbright_face_path()
            if local_face_path and Path(local_face_path).exists():
                active_face_ref = self._upload_to_fal(local_face_path)
            else:
                return {"status": "error", "error": "No face reference available"}
        elif not self._is_url(active_face_ref) and Path(active_face_ref).exists():
            # Local path provided, upload it
            active_face_ref = self._upload_to_fal(active_face_ref)
        
        if not active_face_ref:
            return {"status": "error", "error": "Failed to upload face reference"}
        
        payload = {
            "face_image_url": active_face_ref,
            "image_url": source_image_url,
            "prompt": f"Starbright18, {prompt}",
            "negative_prompt": negative_prompt,
            "ip_adapter_scale": ip_adapter_scale,
            "controlnet_conditioning_scale": controlnet_conditioning_scale,
            "identity_controlnet_conditioning_scale": identity_controlnet_conditioning_scale,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "enhance_face_region": enhance_face_region,
            "controlnet_selection": "canny"
        }
        
        logger.info(f"Transferring identity to: {source_image_url[:50]}...")
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    FAL_INSTANTID_URL,
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    image_data = result.get("image", {})
                    img_url = image_data.get("url", "")
                    
                    if img_url:
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
                                "model": "instantid-lcm"
                            }
                    
                    return {"status": "error", "error": "No image in response"}
                
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
    
    async def batch_transfer(
        self,
        source_images: List[str],
        face_reference_url: Optional[str] = None,
        prompt: str = "professional photography, natural lighting",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Batch process multiple images with identity transfer.
        
        Args:
            source_images: List of image URLs to process
            face_reference_url: Face reference (defaults to Starbright)
            prompt: Styling prompt
            **kwargs: Additional parameters passed to transfer_identity
        
        Returns:
            Dict with results for each image
        """
        results = {
            "status": "success",
            "processed": 0,
            "failed": 0,
            "images": [],
            "errors": []
        }
        
        for i, source_url in enumerate(source_images):
            logger.info(f"Processing image {i+1}/{len(source_images)}")
            
            result = await self.transfer_identity(
                source_image_url=source_url,
                face_reference_url=face_reference_url,
                prompt=prompt,
                filename_prefix=f"batch_{i+1:03d}",
                **kwargs
            )
            
            if result.get("status") == "success":
                results["processed"] += 1
                results["images"].append(result.get("image"))
            else:
                results["failed"] += 1
                results["errors"].append({
                    "source": source_url,
                    "error": result.get("error")
                })
        
        if results["failed"] > 0 and results["processed"] == 0:
            results["status"] = "error"
        elif results["failed"] > 0:
            results["status"] = "partial"
        
        return results
    
    def _get_starbright_face_path(self) -> Optional[str]:
        """Get Starbright face reference as a local file path or None if not found."""
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
    
    async def upload_and_transfer(
        self,
        source_image_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Upload a local source image and transfer identity.
        Useful for processing downloaded influencer images.
        """
        try:
            import fal_client
            
            source_url = fal_client.upload_file(source_image_path)
            logger.info(f"Uploaded source image: {source_url}")
            
            face_ref_path = self.starbright_face_ref
            if Path(face_ref_path).exists():
                face_url = fal_client.upload_file(face_ref_path)
                logger.info(f"Uploaded face reference: {face_url}")
            else:
                face_url = None
            
            return await self.transfer_identity(
                source_image_url=source_url,
                face_reference_url=face_url,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            return {"status": "error", "error": str(e)}


fal_instantid_service = FalInstantIDService()
