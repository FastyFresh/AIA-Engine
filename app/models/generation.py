from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class GenerationParams:
    lora_scale: float = 0.80
    guidance_scale: float = 2.8
    num_inference_steps: int = 30
    aspect_ratio: str = "3:4"
    positive_prompt_additions: List[str] = field(default_factory=list)
    negative_prompt_additions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "lora_scale": self.lora_scale,
            "guidance_scale": self.guidance_scale,
            "num_inference_steps": self.num_inference_steps,
            "aspect_ratio": self.aspect_ratio,
            "positive_prompt_additions": self.positive_prompt_additions,
            "negative_prompt_additions": self.negative_prompt_additions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationParams":
        return cls(
            lora_scale=data.get("lora_scale", 0.80),
            guidance_scale=data.get("guidance_scale", 2.8),
            num_inference_steps=data.get("num_inference_steps", 30),
            aspect_ratio=data.get("aspect_ratio", "3:4"),
            positive_prompt_additions=data.get("positive_prompt_additions", []),
            negative_prompt_additions=data.get("negative_prompt_additions", [])
        )


@dataclass
class GenerationResult:
    status: str
    image_path: Optional[str] = None
    prediction_id: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    params: Optional[GenerationParams] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "image_path": self.image_path,
            "prediction_id": self.prediction_id,
            "model": self.model,
            "prompt": self.prompt,
            "params": self.params.to_dict() if self.params else None,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class GenerationContext:
    influencer_name: str
    influencer_handle: str
    prompt: str
    params: GenerationParams
    result: Optional[GenerationResult] = None
    quality_score: Optional[float] = None
    quality_feedback: Optional[Dict[str, Any]] = None
    approved: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "influencer_name": self.influencer_name,
            "influencer_handle": self.influencer_handle,
            "prompt": self.prompt,
            "params": self.params.to_dict(),
            "result": self.result.to_dict() if self.result else None,
            "quality_score": self.quality_score,
            "quality_feedback": self.quality_feedback,
            "approved": self.approved
        }
