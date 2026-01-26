from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import logging

from app.config import INFLUENCERS, InfluencerConfig
from app.agents.identity_agent import IdentityAgent
from app.agents.reference_agent import ReferenceAgent
from app.agents.quality_agent import QualityAgent
from app.services.content_service import ContentService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GenerationMethod(Enum):
    INSTANT_ID = "instant_id"
    KONTEXT = "kontext"
    FLUX = "flux"
    GROK = "grok"
    TWO_STAGE = "two_stage"
    PULID = "pulid"


class Orchestrator:
    """
    Multi-agent orchestrator for AI influencer content generation.
    
    Current Active Pipeline:
    1. IdentityAgent - Loads influencer persona context
    2. ReferenceAgent - Generates images using LoRA-trained models
    3. QualityAgent - Vision-based quality scoring and approval
    
    Future Pipeline (not yet implemented):
    4. AssetManager - Post-approval persistence and routing
    5. EditingAgent - Image post-processing
    6. PublishingAgent - Platform-specific posting
    7. AnalyticsAgent - Performance tracking
    """
    
    def __init__(self):
        self.identity_agent = IdentityAgent()
        self.reference_agent = ReferenceAgent()
        self.quality_agent = QualityAgent()
        self.content_service = ContentService()
        
        self.generation_method = GenerationMethod.INSTANT_ID
        self.use_reference = True
        self.enable_quality_check = True
        
        logger.info("Orchestrator initialized with core agents (Identity, Reference, Quality)")
    
    def configure(
        self,
        generation_method: str = "instant_id",
        use_reference: bool = True,
        enable_quality_check: bool = True
    ):
        """Configure the orchestrator's generation settings."""
        self.generation_method = GenerationMethod(generation_method)
        self.use_reference = use_reference
        self.enable_quality_check = enable_quality_check
        
        logger.info(f"Orchestrator configured: method={generation_method}, ref={use_reference}, quality={enable_quality_check}")
    
    async def run_daily_cycle(
        self,
        generation_method: Optional[str] = None,
        use_reference: Optional[bool] = None
    ) -> Dict[str, Any]:
        method = generation_method or self.generation_method.value
        ref = use_reference if use_reference is not None else self.use_reference
        
        logger.info("=" * 60)
        logger.info(f"STARTING DAILY CYCLE (method={method}, reference={ref})")
        logger.info("=" * 60)
        
        cycle_start = datetime.now()
        influencer_results = []
        
        for influencer in INFLUENCERS:
            logger.info(f"\n{'='*40}")
            logger.info(f"Processing influencer: {influencer.name}")
            logger.info(f"{'='*40}")
            
            result = await self._process_influencer(influencer, method, ref)
            influencer_results.append(result)
        
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()
        
        total_images = sum(r.get("content", {}).get("images_generated", 0) for r in influencer_results)
        
        summary = {
            "cycle_id": f"cycle_{cycle_start.strftime('%Y%m%d_%H%M%S')}",
            "started_at": cycle_start.isoformat(),
            "completed_at": cycle_end.isoformat(),
            "duration_seconds": round(duration, 2),
            "generation_method": method,
            "use_reference": ref,
            "influencers_processed": len(influencer_results),
            "total_images_generated": total_images,
            "influencer_results": influencer_results,
            "status": "cycle_complete"
        }
        
        logger.info("=" * 60)
        logger.info(f"DAILY CYCLE COMPLETE - Duration: {duration:.2f}s, Images: {total_images}")
        logger.info("=" * 60)
        
        return summary
    
    async def _process_influencer(
        self,
        influencer: InfluencerConfig,
        method: str,
        use_reference: bool
    ) -> Dict[str, Any]:
        """Process a single influencer through the generation pipeline."""
        identity_context = await self.identity_agent.run(influencer)
        
        content_result = await self.reference_agent.run(
            influencer=influencer,
            identity_context=identity_context,
            use_reference=use_reference,
            generation_method=method
        )
        
        quality_results = []
        if self.enable_quality_check:
            content_items = content_result.get("content_items", [])
            for item in content_items:
                image_path = item.get("image_path")
                if image_path:
                    quality_result = await self._run_quality_check(
                        image_path=image_path,
                        influencer=influencer,
                        prompt=item.get("prompt", ""),
                        generation_params=item.get("generation_params", {})
                    )
                    quality_results.append({
                        "image_path": image_path,
                        "analysis": quality_result
                    })
        
        archived = self.content_service.auto_archive_images(influencer)
        
        return {
            "influencer": influencer.name,
            "identity": identity_context,
            "content": content_result,
            "quality_analysis": quality_results if quality_results else None,
            "archived_count": archived,
            "status": "influencer_complete"
        }
    
    async def generate_single(
        self,
        influencer_name: str,
        prompt: str,
        method: str = "instant_id",
        use_reference: bool = True,
        run_quality_check: bool = True
    ) -> Dict[str, Any]:
        influencer = None
        for inf in INFLUENCERS:
            if inf.name.lower() == influencer_name.lower():
                influencer = inf
                break
        
        if not influencer:
            return {"status": "error", "message": f"Influencer not found: {influencer_name}"}
        
        result = await self.reference_agent.generate_single(
            influencer=influencer,
            prompt=prompt,
            use_reference=use_reference,
            method=method
        )
        
        if self.enable_quality_check and run_quality_check and result.get("status") == "success":
            image_path = result.get("image_path")
            if image_path:
                quality_result = await self._run_quality_check(
                    image_path=image_path,
                    influencer=influencer,
                    prompt=prompt,
                    generation_params=result.get("generation_params", {})
                )
                result["quality_analysis"] = quality_result
        
        archived = self.content_service.auto_archive_images(influencer)
        if archived > 0:
            result["archived_count"] = archived
        
        return result
    
    async def _run_quality_check(
        self,
        image_path: str,
        influencer: InfluencerConfig,
        prompt: str,
        generation_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Running quality check on: {image_path}")
            
            quality_result = await self.quality_agent.analyze_generation(
                image_path=image_path,
                influencer_name=influencer.name,
                influencer_handle=influencer.handle,
                prompt=prompt,
                generation_params=generation_params
            )
            
            result_dict = quality_result.to_dict()
            
            if quality_result.score:
                if quality_result.approved_recommendation:
                    logger.info(f"Quality check PASSED - Score: {quality_result.score.overall:.2f}")
                else:
                    logger.warning(f"Quality check FAILED - Score: {quality_result.score.overall:.2f}")
                    if quality_result.score.issues:
                        logger.warning(f"Issues: {', '.join(quality_result.score.issues[:2])}")
            
            return result_dict
            
        except Exception as e:
            logger.error(f"Quality check error: {e}")
            return {"error": str(e), "analyzed": False}
