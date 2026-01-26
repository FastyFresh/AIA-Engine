import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.agents.base import BaseAgent
from app.tools.vision_client import VisionLLMClient, VisionAnalysis
from app.storage.tuning_repository import TuningProfileRepository
from app.models.tuning import TuningProfile, QualityScore

logger = logging.getLogger(__name__)


@dataclass
class QualityResult:
    analyzed: bool
    score: Optional[QualityScore]
    approved_recommendation: bool
    recommended_params: Dict[str, Any]
    analysis_provider: Optional[str]
    latency_ms: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analyzed": self.analyzed,
            "score": self.score.to_dict() if self.score else None,
            "approved_recommendation": self.approved_recommendation,
            "recommended_params": self.recommended_params,
            "analysis_provider": self.analysis_provider,
            "latency_ms": self.latency_ms,
            "error": self.error
        }


class QualityAgent(BaseAgent):
    
    APPROVAL_THRESHOLD = 0.70
    
    SKIN_WEIGHT = 0.35
    FACE_WEIGHT = 0.30
    LIGHTING_WEIGHT = 0.20
    COMPOSITION_WEIGHT = 0.15
    
    def __init__(self):
        super().__init__("QualityAgent")
        self.vision_client = VisionLLMClient()
        self.tuning_repo = TuningProfileRepository()
        self.enabled = True
    
    async def run(self, *args, **kwargs) -> Dict[str, Any]:
        image_path = kwargs.get("image_path")
        influencer_name = kwargs.get("influencer_name", "")
        influencer_handle = kwargs.get("influencer_handle", "")
        prompt = kwargs.get("prompt", "")
        generation_params = kwargs.get("generation_params", {})
        
        if not image_path:
            return {"error": "No image_path provided"}
        
        result = await self.analyze_generation(
            image_path=image_path,
            influencer_name=influencer_name,
            influencer_handle=influencer_handle,
            prompt=prompt,
            generation_params=generation_params
        )
        
        return result.to_dict()
    
    async def analyze_generation(
        self,
        image_path: str,
        influencer_name: str,
        influencer_handle: str,
        prompt: str,
        generation_params: Dict[str, Any]
    ) -> QualityResult:
        if not self.enabled:
            return QualityResult(
                analyzed=False,
                score=None,
                approved_recommendation=True,
                recommended_params=generation_params,
                analysis_provider=None,
                latency_ms=0,
                error="QualityAgent disabled"
            )
        
        logger.info(f"Analyzing image quality: {image_path}")
        
        analysis = await self.vision_client.analyze_image(image_path)
        
        if not analysis.success:
            logger.warning(f"Vision analysis failed: {analysis.error}")
            return QualityResult(
                analyzed=False,
                score=None,
                approved_recommendation=True,
                recommended_params=generation_params,
                analysis_provider=analysis.provider,
                latency_ms=analysis.latency_ms,
                error=analysis.error
            )
        
        score = QualityScore(
            overall=analysis.overall_score,
            skin_realism=analysis.skin_realism,
            face_consistency=analysis.face_consistency,
            lighting_quality=analysis.lighting_quality,
            composition=analysis.composition,
            issues=analysis.issues,
            recommendations=analysis.recommendations
        )
        
        approved = analysis.overall_score >= self.APPROVAL_THRESHOLD
        
        recommended_params = self._calculate_recommended_params(
            current_params=generation_params,
            score=score,
            influencer_handle=influencer_handle
        )
        
        logger.info(
            f"Quality analysis complete: overall={score.overall:.2f}, "
            f"skin={score.skin_realism:.2f}, face={score.face_consistency:.2f}, "
            f"approved={approved}"
        )
        
        return QualityResult(
            analyzed=True,
            score=score,
            approved_recommendation=approved,
            recommended_params=recommended_params,
            analysis_provider=analysis.provider,
            latency_ms=analysis.latency_ms
        )
    
    def _calculate_recommended_params(
        self,
        current_params: Dict[str, Any],
        score: QualityScore,
        influencer_handle: str
    ) -> Dict[str, Any]:
        recommended = current_params.copy()
        
        current_lora = current_params.get("lora_scale", 0.80)
        current_guidance = current_params.get("guidance_scale", 2.8)
        
        if score.skin_realism < 0.6:
            recommended["lora_scale"] = max(0.70, current_lora - 0.03)
            logger.info(f"Recommending lower LoRA scale due to low skin realism: {recommended['lora_scale']}")
        elif score.skin_realism >= 0.85 and score.face_consistency < 0.7:
            recommended["lora_scale"] = min(0.88, current_lora + 0.02)
            logger.info(f"Recommending higher LoRA scale for face consistency: {recommended['lora_scale']}")
        
        if score.skin_realism < 0.5:
            recommended["guidance_scale"] = max(2.0, current_guidance - 0.3)
        elif score.overall >= 0.85:
            pass
        
        if score.skin_realism < 0.6:
            current_neg = recommended.get("negative_prompt_additions", [])
            if "extra waxy" not in current_neg:
                recommended["negative_prompt_additions"] = current_neg + ["extra smooth", "doll-like"]
        
        return recommended
    
    async def record_feedback(
        self,
        influencer_name: str,
        influencer_handle: str,
        image_path: str,
        prompt: str,
        params: Dict[str, Any],
        approved: bool,
        quality_score: Optional[QualityScore] = None,
        notes: Optional[str] = None
    ) -> TuningProfile:
        profile = self.tuning_repo.add_feedback(
            influencer_name=influencer_name,
            influencer_handle=influencer_handle,
            image_path=image_path,
            prompt=prompt,
            params=params,
            approved=approved,
            quality_score=quality_score,
            notes=notes
        )
        
        if profile.total_generations >= 5:
            self._update_profile_from_feedback(profile)
        
        return profile
    
    def _update_profile_from_feedback(self, profile: TuningProfile):
        recent_approved = [
            f for f in profile.feedback_history[-20:]
            if f.approved and f.params
        ]
        
        if len(recent_approved) < 3:
            return
        
        avg_lora = sum(f.params.get("lora_scale", 0.80) for f in recent_approved) / len(recent_approved)
        avg_guidance = sum(f.params.get("guidance_scale", 2.8) for f in recent_approved) / len(recent_approved)
        
        profile.lora_scale = round(avg_lora, 2)
        profile.guidance_scale = round(avg_guidance, 1)
        
        self.tuning_repo.save_profile(profile)
        logger.info(f"Updated {profile.influencer_name} profile: lora={profile.lora_scale}, guidance={profile.guidance_scale}")
    
    def get_recommended_params(
        self,
        influencer_name: str,
        influencer_handle: str
    ) -> Dict[str, Any]:
        profile = self.tuning_repo.get_profile(influencer_name, influencer_handle)
        return profile.get_recommended_params()
    
    def get_profile_stats(
        self,
        influencer_name: str,
        influencer_handle: str
    ) -> Dict[str, Any]:
        profile = self.tuning_repo.get_profile(influencer_name, influencer_handle)
        
        return {
            "influencer": influencer_name,
            "total_generations": profile.total_generations,
            "approved": profile.approved_count,
            "rejected": profile.rejected_count,
            "approval_rate": f"{profile.approval_rate() * 100:.1f}%",
            "current_params": {
                "lora_scale": profile.lora_scale,
                "guidance_scale": profile.guidance_scale,
                "num_inference_steps": profile.num_inference_steps
            },
            "last_updated": profile.last_updated.isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "approval_threshold": self.APPROVAL_THRESHOLD,
            "vision": self.vision_client.get_status(),
            "profiles": self.tuning_repo.get_stats()
        }
