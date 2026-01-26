import json
import os
import logging
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

from app.models.tuning import TuningProfile, FeedbackEntry, QualityScore

logger = logging.getLogger(__name__)


class TuningProfileRepository:
    
    DEFAULT_STORAGE_PATH = "data/tuning_profiles"
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or self.DEFAULT_STORAGE_PATH)
        self._ensure_storage_dir()
        self._profiles_cache: Dict[str, TuningProfile] = {}
    
    def _ensure_storage_dir(self):
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def _get_profile_path(self, influencer_handle: str) -> Path:
        safe_name = influencer_handle.replace("@", "").lower()
        return self.storage_path / f"{safe_name}_tuning.json"
    
    def get_profile(self, influencer_name: str, influencer_handle: str) -> TuningProfile:
        handle_key = influencer_handle.replace("@", "").lower()
        
        if handle_key in self._profiles_cache:
            return self._profiles_cache[handle_key]
        
        profile_path = self._get_profile_path(influencer_handle)
        
        if profile_path.exists():
            try:
                with open(profile_path, "r") as f:
                    data = json.load(f)
                profile = TuningProfile.from_dict(data)
                logger.info(f"Loaded tuning profile for {influencer_name}")
            except Exception as e:
                logger.error(f"Failed to load profile for {influencer_name}: {e}")
                profile = self._create_default_profile(influencer_name, influencer_handle)
        else:
            profile = self._create_default_profile(influencer_name, influencer_handle)
        
        self._profiles_cache[handle_key] = profile
        return profile
    
    def _create_default_profile(self, influencer_name: str, influencer_handle: str) -> TuningProfile:
        profile = TuningProfile(
            influencer_name=influencer_name,
            influencer_handle=influencer_handle,
            lora_scale=0.77,
            guidance_scale=2.5,
            num_inference_steps=30
        )
        logger.info(f"Created default tuning profile for {influencer_name}")
        return profile
    
    def save_profile(self, profile: TuningProfile) -> bool:
        try:
            profile_path = self._get_profile_path(profile.influencer_handle)
            profile.last_updated = datetime.now()
            
            with open(profile_path, "w") as f:
                json.dump(profile.to_dict(), f, indent=2)
            
            handle_key = profile.influencer_handle.replace("@", "").lower()
            self._profiles_cache[handle_key] = profile
            
            logger.info(f"Saved tuning profile for {profile.influencer_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            return False
    
    def add_feedback(
        self,
        influencer_name: str,
        influencer_handle: str,
        image_path: str,
        prompt: str,
        params: Dict,
        approved: bool,
        quality_score: Optional[QualityScore] = None,
        notes: Optional[str] = None
    ) -> TuningProfile:
        profile = self.get_profile(influencer_name, influencer_handle)
        
        entry = FeedbackEntry(
            image_path=image_path,
            prompt=prompt,
            params=params,
            quality_score=quality_score,
            approved=approved,
            notes=notes
        )
        
        profile.add_feedback(entry)
        self.save_profile(profile)
        
        return profile
    
    def update_recommended_params(
        self,
        influencer_handle: str,
        lora_scale: Optional[float] = None,
        guidance_scale: Optional[float] = None,
        num_inference_steps: Optional[int] = None
    ) -> Optional[TuningProfile]:
        handle_key = influencer_handle.replace("@", "").lower()
        
        if handle_key not in self._profiles_cache:
            logger.warning(f"Profile not found for {influencer_handle}")
            return None
        
        profile = self._profiles_cache[handle_key]
        
        if lora_scale is not None:
            profile.lora_scale = max(profile.lora_scale_min, min(profile.lora_scale_max, lora_scale))
        if guidance_scale is not None:
            profile.guidance_scale = max(profile.guidance_scale_min, min(profile.guidance_scale_max, guidance_scale))
        if num_inference_steps is not None:
            profile.num_inference_steps = num_inference_steps
        
        self.save_profile(profile)
        return profile
    
    def get_all_profiles(self) -> List[TuningProfile]:
        profiles = []
        
        for profile_file in self.storage_path.glob("*_tuning.json"):
            try:
                with open(profile_file, "r") as f:
                    data = json.load(f)
                profiles.append(TuningProfile.from_dict(data))
            except Exception as e:
                logger.error(f"Failed to load profile {profile_file}: {e}")
        
        return profiles
    
    def get_stats(self) -> Dict:
        profiles = self.get_all_profiles()
        
        return {
            "total_profiles": len(profiles),
            "profiles": [
                {
                    "influencer": p.influencer_name,
                    "total_generations": p.total_generations,
                    "approval_rate": f"{p.approval_rate() * 100:.1f}%",
                    "current_lora_scale": p.lora_scale,
                    "current_guidance": p.guidance_scale
                }
                for p in profiles
            ]
        }
