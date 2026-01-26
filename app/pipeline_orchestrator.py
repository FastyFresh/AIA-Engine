"""
PipelineOrchestrator - Orchestrates the full daily content automation pipeline

Integrates all pipeline agents:
1. PlannerAgent - Creates daily task list
2. Seedream4Service - Image generation with dual-reference
3. QualityAgent - Vision-based quality scoring
4. PackagingAgent - Creates post packages
5. TwitterPosterAgent - Automated Twitter posting
6. ManualQueueAgent - IG/TikTok queue management
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from app.config import INFLUENCERS, InfluencerConfig
from app.pipeline_config import (
    get_pipeline_config,
    pipeline_settings,
    InfluencerPipelineConfig
)
from app.agents.planner_agent import PlannerAgent, DailyPlan, GenerationTask
from app.agents.caption_agent import CaptionAgent
from app.agents.packaging_agent import PackagingAgent, PostPackage
from app.agents.reddit_poster_agent import RedditPosterAgent
from app.agents.twitter_poster_agent import TwitterPosterAgent
from app.agents.manual_queue_agent import ManualQueueAgent
from app.agents.face_swap_agent import FaceSwapAgent
from app.agents.reference_agent import ReferenceAgent
from app.agents.quality_agent import QualityAgent

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates the full daily content automation pipeline.
    
    Pipeline stages:
    1. PLAN: Generate daily task list
    2. GENERATE: Create images with Seedream4 dual-reference
    3. REVIEW: Gallery-based approval workflow
    4. PACKAGE: Create post packages per platform
    5. DISTRIBUTE: Post to Twitter, queue IG/TikTok
    6. LOG: Record all activities
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        
        self.planner = PlannerAgent()
        self.caption_agent = CaptionAgent()
        self.packager = PackagingAgent()
        self.reddit_poster = RedditPosterAgent()
        self.twitter_poster = TwitterPosterAgent()
        self.manual_queue = ManualQueueAgent()
        self.face_swap = FaceSwapAgent()
        self.reference_agent = ReferenceAgent()
        self.quality_agent = QualityAgent()
        
        logger.info("PipelineOrchestrator initialized with all agents")
    
    async def run_daily_pipeline(
        self,
        influencer: InfluencerConfig = None,
        dry_run: bool = False,
        skip_generation: bool = False,
        skip_posting: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete daily automation pipeline.
        
        Args:
            influencer: Specific influencer to process (None = all)
            dry_run: If True, simulate without API calls
            skip_generation: If True, use existing approved images
            skip_posting: If True, create packages but don't post
        """
        pipeline_start = datetime.now()
        pipeline_id = f"pipeline_{pipeline_start.strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("=" * 60)
        logger.info(f"STARTING DAILY PIPELINE: {pipeline_id}")
        logger.info(f"Dry run: {dry_run}, Skip generation: {skip_generation}, Skip posting: {skip_posting}")
        logger.info("=" * 60)
        
        influencers = [influencer] if influencer else INFLUENCERS
        
        results = {
            "pipeline_id": pipeline_id,
            "started_at": pipeline_start.isoformat(),
            "dry_run": dry_run,
            "influencer_results": []
        }
        
        for inf in influencers:
            try:
                inf_result = await self._process_influencer_pipeline(
                    influencer=inf,
                    dry_run=dry_run,
                    skip_generation=skip_generation,
                    skip_posting=skip_posting
                )
                results["influencer_results"].append(inf_result)
            except Exception as e:
                logger.error(f"Error processing {inf.name}: {e}")
                results["influencer_results"].append({
                    "influencer": inf.name,
                    "status": "error",
                    "error": str(e)
                })
        
        pipeline_end = datetime.now()
        duration = (pipeline_end - pipeline_start).total_seconds()
        
        results["completed_at"] = pipeline_end.isoformat()
        results["duration_seconds"] = round(duration, 2)
        results["status"] = "complete"
        
        total_posts = sum(
            r.get("distribution", {}).get("total_posted", 0) 
            for r in results["influencer_results"]
        )
        total_queued = sum(
            r.get("manual_queue", {}).get("queued", 0) 
            for r in results["influencer_results"]
        )
        
        results["summary"] = {
            "influencers_processed": len(influencers),
            "total_posts_made": total_posts,
            "total_items_queued": total_queued,
            "duration_seconds": round(duration, 2)
        }
        
        logger.info("=" * 60)
        logger.info(f"PIPELINE COMPLETE: {total_posts} posts made, {total_queued} items queued")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info("=" * 60)
        
        return results
    
    async def _process_influencer_pipeline(
        self,
        influencer: InfluencerConfig,
        dry_run: bool = False,
        skip_generation: bool = False,
        skip_posting: bool = False
    ) -> Dict[str, Any]:
        """Process pipeline for a single influencer"""
        handle = influencer.handle.replace("@", "").lower()
        config = get_pipeline_config(handle)
        
        logger.info(f"\n{'='*40}")
        logger.info(f"Processing influencer: {influencer.name}")
        logger.info(f"{'='*40}")
        
        result = {
            "influencer": influencer.name,
            "handle": influencer.handle
        }
        
        plan = await self.planner.create_daily_plan(influencer)
        result["plan"] = {
            "plan_id": plan.plan_id,
            "total_tasks": plan.total_tasks,
            "tasks_by_platform": plan.tasks_by_platform
        }
        logger.info(f"Plan created: {plan.total_tasks} tasks")
        
        approved_images = []
        if skip_generation:
            approved_images = self._get_existing_approved_images(influencer)
            result["generation"] = {
                "skipped": True,
                "existing_approved": len(approved_images)
            }
        else:
            generation_result = await self._run_generation_cycle(
                influencer=influencer,
                tasks=plan.tasks,
                config=config,
                dry_run=dry_run
            )
            approved_images = generation_result.get("approved_images", [])
            result["generation"] = generation_result
        
        if not approved_images:
            logger.warning(f"No approved images for {influencer.name}, skipping packaging")
            result["packaging"] = {"skipped": True, "reason": "no_approved_images"}
            result["distribution"] = {"skipped": True}
            result["manual_queue"] = {"skipped": True}
            result["status"] = "no_content"
            return result
        
        tasks_as_dicts = [t.model_dump() for t in plan.tasks]
        packaging_result = await self.packager.create_packages(
            influencer=influencer,
            tasks=tasks_as_dicts,
            approved_images=approved_images
        )
        result["packaging"] = {
            "total_packages": packaging_result.get("total_packages", 0),
            "by_platform": packaging_result.get("by_platform", {})
        }
        
        if skip_posting:
            result["distribution"] = {"skipped": True, "reason": "skip_posting=True"}
            result["manual_queue"] = {"skipped": True}
        else:
            reddit_packages = [
                PostPackage(**p) for p in 
                packaging_result.get("packages", {}).get("reddit", [])
            ]
            twitter_packages = [
                PostPackage(**p) for p in 
                packaging_result.get("packages", {}).get("twitter", [])
            ]
            
            distribution_result = await self._distribute_content(
                reddit_packages=reddit_packages,
                twitter_packages=twitter_packages,
                dry_run=dry_run
            )
            result["distribution"] = distribution_result
            
            ig_packages = [
                PostPackage(**p) for p in 
                packaging_result.get("packages", {}).get("instagram_manual", [])
            ]
            tiktok_packages = [
                PostPackage(**p) for p in 
                packaging_result.get("packages", {}).get("tiktok_manual", [])
            ]
            
            manual_packages = ig_packages + tiktok_packages
            if manual_packages:
                queue_items = await self.manual_queue.add_batch_to_queue(manual_packages)
                result["manual_queue"] = {
                    "queued": len(queue_items),
                    "instagram": len([i for i in queue_items if i.platform == "instagram_manual"]),
                    "tiktok": len([i for i in queue_items if i.platform == "tiktok_manual"])
                }
            else:
                result["manual_queue"] = {"queued": 0}
        
        result["status"] = "complete"
        return result
    
    async def _run_generation_cycle(
        self,
        influencer: InfluencerConfig,
        tasks: List[GenerationTask],
        config: InfluencerPipelineConfig,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Run the generation and curation cycle using direct agent calls"""
        handle = influencer.handle.replace("@", "").lower()
        generated_images = []
        
        total_needed = config.quotas.reddit + config.quotas.twitter + config.quotas.instagram_manual + config.quotas.tiktok_manual
        
        logger.info(f"Generating {total_needed} images for {influencer.name}")
        
        if dry_run:
            return {
                "dry_run": True,
                "would_generate": total_needed,
                "tasks_planned": len(tasks),
                "approved_images": []
            }
        
        for i, task in enumerate(tasks[:total_needed]):
            try:
                prompt = await self.planner.get_generation_prompt(task)
                logger.info(f"Generating image {i+1}/{total_needed}: {task.task_id}")
                
                gen_result = await self.reference_agent.generate_lora_image(
                    influencer=influencer,
                    prompt=prompt,
                    num_images=1
                )
                
                if gen_result.get("status") == "success":
                    images = gen_result.get("images", [])
                    for img in images:
                        img_path = img.get("path", img.get("image_path", ""))
                        if img_path:
                            quality_result = await self.quality_agent.analyze_generation(
                                image_path=img_path,
                                influencer_name=influencer.name,
                                influencer_handle=influencer.handle,
                                prompt=prompt,
                                generation_params={}
                            )
                            score = quality_result.score.overall if quality_result.score else 0.75
                            
                            generated_images.append({
                                "path": img_path,
                                "task": task.model_dump(),
                                "score": score,
                                "quality_analysis": quality_result.to_dict() if quality_result else None
                            })
                            logger.info(f"Generated image: {img_path} (score: {score:.2f})")
                else:
                    logger.warning(f"Generation returned non-success: {gen_result}")
                
            except Exception as e:
                logger.error(f"Generation failed for task {task.task_id}: {e}")
        
        if config.face_swap_all and generated_images:
            logger.info(f"Applying face swap to {len(generated_images)} images")
            for img in generated_images:
                try:
                    swap_result = await self.face_swap.swap_face(
                        target_image_path=img["path"],
                        influencer=influencer
                    )
                    if swap_result.get("status") == "success":
                        new_path = swap_result.get("output_path", swap_result.get("image_path", img["path"]))
                        img["original_path"] = img["path"]
                        img["path"] = new_path
                        img["face_swapped"] = True
                        logger.info(f"Face swapped: {new_path}")
                except Exception as e:
                    logger.error(f"Face swap failed for {img['path']}: {e}")
                    img["face_swapped"] = False
        
        approved_images = []
        pending_images = []
        rejected_images = []
        
        for img in generated_images:
            score = img.get("score", 0)
            if score >= config.quality_thresholds.auto_approve:
                approved_images.append(img["path"])
            elif score >= config.quality_thresholds.pending_min:
                pending_images.append(img["path"])
            else:
                rejected_images.append(img["path"])
        
        curation_result = await self.curator.curate_batch(
            images=generated_images,
            influencer=influencer,
            dry_run=False
        )
        
        return {
            "generated": len(generated_images),
            "approved": len(approved_images),
            "pending": len(pending_images),
            "rejected": len(rejected_images),
            "approved_images": approved_images,
            "pending_images": pending_images,
            "curation_details": curation_result
        }
    
    async def _distribute_content(
        self,
        reddit_packages: List[PostPackage],
        twitter_packages: List[PostPackage],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Distribute content to Reddit and Twitter"""
        reddit_result = {"skipped": True}
        twitter_result = {"skipped": True}
        
        if reddit_packages:
            reddit_result = await self.reddit_poster.post_batch(
                packages=reddit_packages,
                dry_run=dry_run
            )
        
        if twitter_packages:
            twitter_result = await self.twitter_poster.post_batch(
                packages=twitter_packages,
                dry_run=dry_run
            )
        
        return {
            "reddit": reddit_result,
            "twitter": twitter_result,
            "total_posted": (
                reddit_result.get("successful", 0) + 
                twitter_result.get("successful", 0)
            ),
            "total_failed": (
                reddit_result.get("failed", 0) + 
                twitter_result.get("failed", 0)
            )
        }
    
    def _get_existing_approved_images(
        self,
        influencer: InfluencerConfig
    ) -> List[str]:
        """Get list of already approved images"""
        handle = influencer.handle.replace("@", "").lower()
        final_dir = Path(f"content/final/{handle}")
        
        if not final_dir.exists():
            return []
        
        images = list(final_dir.glob("*.png")) + list(final_dir.glob("*.jpg"))
        images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return [str(p) for p in images[:20]]
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline configuration and status"""
        return {
            "reddit_configured": self.reddit_poster.is_configured(),
            "twitter_configured": self.twitter_poster.is_configured(),
            "dry_run_mode": pipeline_settings.DRY_RUN,
            "influencers": [
                {
                    "name": inf.name,
                    "handle": inf.handle,
                    "quotas": get_pipeline_config(inf.handle.replace("@", "").lower()).quotas.model_dump()
                }
                for inf in INFLUENCERS
            ]
        }
    
    async def get_manual_queue_stats(self) -> Dict[str, Any]:
        """Get manual queue statistics"""
        return await self.manual_queue.get_queue_stats()
