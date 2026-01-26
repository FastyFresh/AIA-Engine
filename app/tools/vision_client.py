import os
import base64
import asyncio
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

VISION_TIMEOUT_SECONDS = 30


@dataclass
class VisionAnalysis:
    success: bool
    overall_score: float
    skin_realism: float
    face_consistency: float
    lighting_quality: float
    composition: float
    issues: list
    recommendations: list
    provider: str
    latency_ms: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "overall_score": self.overall_score,
            "skin_realism": self.skin_realism,
            "face_consistency": self.face_consistency,
            "lighting_quality": self.lighting_quality,
            "composition": self.composition,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "provider": self.provider,
            "latency_ms": self.latency_ms,
            "error": self.error
        }


class VisionLLMClient:
    
    SCORING_PROMPT = """Analyze this AI-generated image of a social media influencer for production quality.

Score each category from 0.0 to 1.0:

1. **Skin Realism** (0.0-1.0): Does the skin look like real human skin with pores, natural texture, and imperfections? Or does it look waxy, plastic, airbrushed, or CGI?
   - 0.0-0.3: Very waxy/plastic/CGI looking
   - 0.4-0.6: Some unrealistic areas
   - 0.7-0.8: Mostly realistic with minor issues
   - 0.9-1.0: Hyper-realistic, indistinguishable from real photography

2. **Face Consistency** (0.0-1.0): Does the face look natural and consistent? Are features proportional? Any distortions or uncanny valley effects?
   - 0.0-0.3: Major distortions or uncanny valley
   - 0.4-0.6: Some inconsistencies
   - 0.7-0.8: Natural looking with minor issues
   - 0.9-1.0: Perfect, natural face

3. **Lighting Quality** (0.0-1.0): Is the lighting natural and flattering? Does it enhance the image?
   - 0.0-0.3: Harsh, unnatural, or flat
   - 0.4-0.6: Acceptable but could be better
   - 0.7-0.8: Good, professional lighting
   - 0.9-1.0: Excellent, editorial quality

4. **Composition** (0.0-1.0): Is the framing, focus, and overall composition suitable for social media?
   - 0.0-0.3: Poor framing or focus
   - 0.4-0.6: Acceptable
   - 0.7-0.8: Good composition
   - 0.9-1.0: Excellent, professional quality

Respond in this exact JSON format:
{
    "skin_realism": 0.0,
    "face_consistency": 0.0,
    "lighting_quality": 0.0,
    "composition": 0.0,
    "issues": ["issue1", "issue2"],
    "recommendations": ["recommendation1", "recommendation2"]
}

Be critical and honest. If the skin looks waxy or plastic, score it low. Issues should identify specific problems. Recommendations should suggest parameter adjustments (e.g., "lower LoRA scale", "add more skin texture prompts")."""

    def __init__(self):
        self._anthropic_client = None
        self._openai_client = None
        self._initialized = False
    
    def _init_clients(self):
        if self._initialized:
            return
        
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                logger.info("Vision: Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Vision: Failed to init Anthropic: {e}")
        
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            try:
                import openai
                self._openai_client = openai.OpenAI(api_key=openai_key)
                logger.info("Vision: OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Vision: Failed to init OpenAI: {e}")
        
        self._initialized = True
    
    def _encode_image(self, image_path: str) -> Optional[str]:
        try:
            path = Path(image_path)
            if not path.exists():
                logger.error(f"Image not found: {image_path}")
                return None
            
            with open(path, "rb") as f:
                return base64.standard_b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to encode image: {e}")
            return None
    
    def _get_media_type(self, image_path: str) -> str:
        try:
            with open(image_path, "rb") as f:
                header = f.read(12)
            
            if header[:8] == b'\x89PNG\r\n\x1a\n':
                return "image/png"
            elif header[:2] == b'\xff\xd8':
                return "image/jpeg"
            elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
                return "image/webp"
            elif header[:6] in (b'GIF87a', b'GIF89a'):
                return "image/gif"
            else:
                ext = Path(image_path).suffix.lower()
                return {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".webp": "image/webp",
                    ".gif": "image/gif"
                }.get(ext, "image/png")
        except Exception as e:
            logger.warning(f"Failed to detect image type, falling back to extension: {e}")
            ext = Path(image_path).suffix.lower()
            return {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
                ".gif": "image/gif"
            }.get(ext, "image/png")
    
    async def analyze_image(
        self,
        image_path: str,
        provider: Optional[str] = None
    ) -> VisionAnalysis:
        self._init_clients()
        
        image_data = self._encode_image(image_path)
        if not image_data:
            return VisionAnalysis(
                success=False,
                overall_score=0.0,
                skin_realism=0.0,
                face_consistency=0.0,
                lighting_quality=0.0,
                composition=0.0,
                issues=["Failed to load image"],
                recommendations=[],
                provider="none",
                latency_ms=0,
                error="Image not found or could not be loaded"
            )
        
        if provider == "anthropic" or (provider is None and self._anthropic_client):
            return await self._analyze_with_anthropic(image_path, image_data)
        elif provider == "openai" or (provider is None and self._openai_client):
            return await self._analyze_with_openai(image_path, image_data)
        else:
            return VisionAnalysis(
                success=False,
                overall_score=0.0,
                skin_realism=0.0,
                face_consistency=0.0,
                lighting_quality=0.0,
                composition=0.0,
                issues=["No vision provider available"],
                recommendations=["Configure ANTHROPIC_API_KEY or OPENAI_API_KEY"],
                provider="none",
                latency_ms=0,
                error="No vision API available"
            )
    
    async def _analyze_with_anthropic(self, image_path: str, image_data: str) -> VisionAnalysis:
        start_time = time.time()
        
        try:
            media_type = self._get_media_type(image_path)
            
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._anthropic_client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": media_type,
                                            "data": image_data
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": self.SCORING_PROMPT
                                    }
                                ]
                            }
                        ]
                    )
                ),
                timeout=VISION_TIMEOUT_SECONDS
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            content = response.content[0].text if response.content else ""
            return self._parse_response(content, "anthropic", latency_ms)
            
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            return VisionAnalysis(
                success=False,
                overall_score=0.0,
                skin_realism=0.0,
                face_consistency=0.0,
                lighting_quality=0.0,
                composition=0.0,
                issues=["Vision analysis timed out"],
                recommendations=[],
                provider="anthropic",
                latency_ms=latency_ms,
                error=f"Timeout after {VISION_TIMEOUT_SECONDS}s"
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Anthropic vision error: {e}")
            return VisionAnalysis(
                success=False,
                overall_score=0.0,
                skin_realism=0.0,
                face_consistency=0.0,
                lighting_quality=0.0,
                composition=0.0,
                issues=["Vision analysis failed"],
                recommendations=[],
                provider="anthropic",
                latency_ms=latency_ms,
                error=str(e)
            )
    
    async def _analyze_with_openai(self, image_path: str, image_data: str) -> VisionAnalysis:
        start_time = time.time()
        
        try:
            media_type = self._get_media_type(image_path)
            
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        max_tokens=1000,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{media_type};base64,{image_data}"
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": self.SCORING_PROMPT
                                    }
                                ]
                            }
                        ]
                    )
                ),
                timeout=VISION_TIMEOUT_SECONDS
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            content = response.choices[0].message.content if response.choices else ""
            return self._parse_response(content, "openai", latency_ms)
            
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            return VisionAnalysis(
                success=False,
                overall_score=0.0,
                skin_realism=0.0,
                face_consistency=0.0,
                lighting_quality=0.0,
                composition=0.0,
                issues=["Vision analysis timed out"],
                recommendations=[],
                provider="openai",
                latency_ms=latency_ms,
                error=f"Timeout after {VISION_TIMEOUT_SECONDS}s"
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"OpenAI vision error: {e}")
            return VisionAnalysis(
                success=False,
                overall_score=0.0,
                skin_realism=0.0,
                face_consistency=0.0,
                lighting_quality=0.0,
                composition=0.0,
                issues=["Vision analysis failed"],
                recommendations=[],
                provider="openai",
                latency_ms=latency_ms,
                error=str(e)
            )
    
    def _parse_response(self, content: str, provider: str, latency_ms: float) -> VisionAnalysis:
        import json
        import re
        
        try:
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            data = json.loads(json_match.group())
            
            skin = float(data.get("skin_realism", 0.5))
            face = float(data.get("face_consistency", 0.5))
            lighting = float(data.get("lighting_quality", 0.5))
            composition = float(data.get("composition", 0.5))
            
            overall = (skin * 0.35 + face * 0.30 + lighting * 0.20 + composition * 0.15)
            
            return VisionAnalysis(
                success=True,
                overall_score=round(overall, 2),
                skin_realism=round(skin, 2),
                face_consistency=round(face, 2),
                lighting_quality=round(lighting, 2),
                composition=round(composition, 2),
                issues=data.get("issues", []),
                recommendations=data.get("recommendations", []),
                provider=provider,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            logger.error(f"Failed to parse vision response: {e}")
            return VisionAnalysis(
                success=False,
                overall_score=0.5,
                skin_realism=0.5,
                face_consistency=0.5,
                lighting_quality=0.5,
                composition=0.5,
                issues=["Failed to parse scoring response"],
                recommendations=[],
                provider=provider,
                latency_ms=latency_ms,
                error=f"Parse error: {e}"
            )
    
    def get_status(self) -> Dict[str, Any]:
        self._init_clients()
        
        return {
            "providers": {
                "anthropic": {
                    "available": self._anthropic_client is not None
                },
                "openai": {
                    "available": self._openai_client is not None
                }
            },
            "timeout_seconds": VISION_TIMEOUT_SECONDS
        }
