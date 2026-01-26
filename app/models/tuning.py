from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class QualityScore:
    overall: float
    skin_realism: float
    face_consistency: float
    lighting_quality: float
    composition: float
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "skin_realism": self.skin_realism,
            "face_consistency": self.face_consistency,
            "lighting_quality": self.lighting_quality,
            "composition": self.composition,
            "issues": self.issues,
            "recommendations": self.recommendations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityScore":
        return cls(
            overall=data.get("overall", 0.0),
            skin_realism=data.get("skin_realism", 0.0),
            face_consistency=data.get("face_consistency", 0.0),
            lighting_quality=data.get("lighting_quality", 0.0),
            composition=data.get("composition", 0.0),
            issues=data.get("issues", []),
            recommendations=data.get("recommendations", [])
        )


@dataclass
class FeedbackEntry:
    image_path: str
    prompt: str
    params: Dict[str, Any]
    quality_score: Optional[QualityScore]
    approved: bool
    timestamp: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_path": self.image_path,
            "prompt": self.prompt,
            "params": self.params,
            "quality_score": self.quality_score.to_dict() if self.quality_score else None,
            "approved": self.approved,
            "timestamp": self.timestamp.isoformat(),
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedbackEntry":
        return cls(
            image_path=data["image_path"],
            prompt=data["prompt"],
            params=data["params"],
            quality_score=QualityScore.from_dict(data["quality_score"]) if data.get("quality_score") else None,
            approved=data["approved"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
            notes=data.get("notes")
        )


@dataclass
class TuningProfile:
    influencer_name: str
    influencer_handle: str
    
    lora_scale: float = 0.80
    guidance_scale: float = 2.8
    num_inference_steps: int = 30
    
    lora_scale_min: float = 0.70
    lora_scale_max: float = 0.90
    guidance_scale_min: float = 2.0
    guidance_scale_max: float = 4.0
    
    positive_prompt_additions: List[str] = field(default_factory=list)
    negative_prompt_additions: List[str] = field(default_factory=list)
    
    total_generations: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    
    feedback_history: List[FeedbackEntry] = field(default_factory=list)
    
    last_updated: datetime = field(default_factory=datetime.now)
    
    def approval_rate(self) -> float:
        if self.total_generations == 0:
            return 0.0
        return self.approved_count / self.total_generations
    
    def add_feedback(self, entry: FeedbackEntry):
        self.feedback_history.append(entry)
        self.total_generations += 1
        if entry.approved:
            self.approved_count += 1
        else:
            self.rejected_count += 1
        self.last_updated = datetime.now()
    
    def get_recommended_params(self) -> Dict[str, Any]:
        return {
            "lora_scale": self.lora_scale,
            "guidance_scale": self.guidance_scale,
            "num_inference_steps": self.num_inference_steps,
            "positive_prompt_additions": self.positive_prompt_additions,
            "negative_prompt_additions": self.negative_prompt_additions
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "influencer_name": self.influencer_name,
            "influencer_handle": self.influencer_handle,
            "lora_scale": self.lora_scale,
            "guidance_scale": self.guidance_scale,
            "num_inference_steps": self.num_inference_steps,
            "lora_scale_min": self.lora_scale_min,
            "lora_scale_max": self.lora_scale_max,
            "guidance_scale_min": self.guidance_scale_min,
            "guidance_scale_max": self.guidance_scale_max,
            "positive_prompt_additions": self.positive_prompt_additions,
            "negative_prompt_additions": self.negative_prompt_additions,
            "total_generations": self.total_generations,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "feedback_history": [f.to_dict() for f in self.feedback_history[-50:]],
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TuningProfile":
        profile = cls(
            influencer_name=data["influencer_name"],
            influencer_handle=data["influencer_handle"],
            lora_scale=data.get("lora_scale", 0.80),
            guidance_scale=data.get("guidance_scale", 2.8),
            num_inference_steps=data.get("num_inference_steps", 30),
            lora_scale_min=data.get("lora_scale_min", 0.70),
            lora_scale_max=data.get("lora_scale_max", 0.90),
            guidance_scale_min=data.get("guidance_scale_min", 2.0),
            guidance_scale_max=data.get("guidance_scale_max", 4.0),
            positive_prompt_additions=data.get("positive_prompt_additions", []),
            negative_prompt_additions=data.get("negative_prompt_additions", []),
            total_generations=data.get("total_generations", 0),
            approved_count=data.get("approved_count", 0),
            rejected_count=data.get("rejected_count", 0),
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else datetime.now()
        )
        
        if data.get("feedback_history"):
            profile.feedback_history = [FeedbackEntry.from_dict(f) for f in data["feedback_history"]]
        
        return profile
