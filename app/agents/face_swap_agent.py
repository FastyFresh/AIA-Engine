import os
import logging
from typing import Optional, Dict, Any
from app.tools.replicate_client import ReplicateClient
from app.config import INFLUENCERS, InfluencerConfig

logger = logging.getLogger(__name__)


class FaceSwapAgent:
    
    def __init__(self):
        self.replicate_client = ReplicateClient()
        self._influencer_cache: Dict[str, InfluencerConfig] = {
            inf.name.lower(): inf for inf in INFLUENCERS
        }
    
    def get_influencer_config(self, influencer_name: str) -> Optional[InfluencerConfig]:
        return self._influencer_cache.get(influencer_name.lower())
    
    def get_canonical_face_path(self, influencer_name: str) -> Optional[str]:
        config = self.get_influencer_config(influencer_name)
        if config and config.canonical_face_path:
            if os.path.exists(config.canonical_face_path):
                return config.canonical_face_path
            logger.warning(f"Canonical face path not found: {config.canonical_face_path}")
        return None
    
    async def swap_face(
        self,
        target_image_path: str,
        influencer_name: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        source_face_path = self.get_canonical_face_path(influencer_name)
        
        if not source_face_path:
            return {
                "status": "error",
                "error": f"No canonical face configured for influencer: {influencer_name}"
            }
        
        if not os.path.exists(target_image_path):
            return {
                "status": "error",
                "error": f"Target image not found: {target_image_path}"
            }
        
        config = self.get_influencer_config(influencer_name)
        influencer_slug = influencer_name.lower().replace(" ", "_")
        
        if output_dir is None:
            output_dir = f"content/raw/{influencer_slug}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Face swap: {target_image_path} -> {influencer_name}")
        
        result = await self.replicate_client.face_swap_simple(
            target_image_path=target_image_path,
            source_face_path=source_face_path,
            output_dir=output_dir,
            filename_prefix=f"{influencer_slug}_swapped"
        )
        
        if result.get("status") == "success":
            logger.info(f"Face swap successful: {result.get('image_path')}")
        else:
            logger.error(f"Face swap failed: {result.get('error')}")
        
        return result
    
    async def swap_face_custom(
        self,
        target_image_path: str,
        source_face_path: str,
        output_dir: str = "content/raw",
        filename_prefix: str = "swapped",
        hair_source: str = "target",
        upscale: bool = True,
        detailer: bool = False,
        user_gender: str = "a woman"
    ) -> Dict[str, Any]:
        if not os.path.exists(target_image_path):
            return {
                "status": "error",
                "error": f"Target image not found: {target_image_path}"
            }
        
        if not os.path.exists(source_face_path):
            return {
                "status": "error",
                "error": f"Source face not found: {source_face_path}"
            }
        
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Custom face swap: {source_face_path} -> {target_image_path}")
        
        result = await self.replicate_client.face_swap(
            target_image_path=target_image_path,
            source_face_path=source_face_path,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            hair_source=hair_source,
            upscale=upscale,
            detailer=detailer,
            user_gender=user_gender
        )
        
        return result
    
    async def process_generated_image(
        self,
        image_path: str,
        influencer_name: str,
        apply_face_swap: bool = True
    ) -> Dict[str, Any]:
        if not apply_face_swap:
            return {
                "status": "skipped",
                "original_path": image_path,
                "message": "Face swap disabled"
            }
        
        result = await self.swap_face(
            target_image_path=image_path,
            influencer_name=influencer_name
        )
        
        return {
            "status": result.get("status"),
            "original_path": image_path,
            "swapped_path": result.get("image_path"),
            "error": result.get("error")
        }
