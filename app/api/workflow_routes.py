"""Content workflow routes (approve, reject, auto-post)."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pathlib import Path
import shutil
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["Workflow"])

from app.config import INFLUENCERS
from app.agents.quality_agent import QualityAgent
from app.services.storage_manager import storage_manager

quality_agent = QualityAgent()

APPROVAL_STATUS_FILE = "data/approval_status.json"


def load_approval_status() -> dict:
    try:
        if os.path.exists(APPROVAL_STATUS_FILE):
            with open(APPROVAL_STATUS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load approval status: {e}")
    return {}


def save_approval_status(status: dict):
    try:
        os.makedirs(os.path.dirname(APPROVAL_STATUS_FILE), exist_ok=True)
        with open(APPROVAL_STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save approval status: {e}")


async def _auto_post_to_twitter(image_path: str, influencer_id: str = "starbright_monroe") -> dict:
    """Auto-generate caption, hashtags, CTA and post to Twitter/X"""
    from app.agents.starbright_caption_generator import StarbrightCaptionGenerator
    from app.agents.twitter_oauth2_agent import TwitterOAuth2Agent
    
    try:
        caption_generator = StarbrightCaptionGenerator()
        twitter_agent = TwitterOAuth2Agent()
        
        logger.info(f"Auto-posting to X: {image_path}")
        
        caption_result = await caption_generator.generate_caption(
            hero_image_filename=Path(image_path).name
        )
        caption = caption_result.get("caption", "")
        
        if not caption:
            return {"error": "Failed to generate caption"}
        
        compose_result = await twitter_agent.compose_post(
            caption=caption,
            influencer=influencer_id,
            include_cta=True,
            include_hashtags=True,
            media_filename=Path(image_path).name,
            max_hashtags=5,
            use_dynamic_cta=True
        )
        
        full_text = compose_result.get("composed_text", caption)
        
        post_result = await twitter_agent.post_with_media(
            text=full_text,
            media_path=image_path,
            influencer=influencer_id
        )
        
        logger.info(f"Auto-post result: {post_result.get('status')}")
        
        return {
            "status": post_result.get("status"),
            "tweet_url": post_result.get("tweet_url"),
            "caption": caption,
            "full_text": full_text,
            "hashtags": compose_result.get("hashtags", []),
            "cta": compose_result.get("cta_used")
        }
        
    except Exception as e:
        logger.error(f"Auto-post to Twitter failed: {e}")
        return {"error": str(e)}


@router.get("/approve")
async def workflow_approve_image(
    image_path: str = Query(..., description="Path to image file"),
    influencer: str = Query(default="Luna Vale", description="Influencer name"),
    auto_post: bool = Query(default=False, description="Auto-post to X after approval (Starbright only)")
):
    logger.info(f"Approving image: {image_path}")
    
    inf_config = None
    for inf in INFLUENCERS:
        if inf.name.lower() == influencer.lower():
            inf_config = inf
            break
    
    if not inf_config:
        raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")
    
    source_path = Path(image_path)
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    handle = inf_config.handle.replace("@", "").lower()
    final_dir = Path(f"content/final/{handle}")
    
    approve_result = await storage_manager.approve_with_offload(
        source_path=source_path,
        final_dir=final_dir,
        delete_source=False
    )
    
    if approve_result["status"] == "error":
        error_msg = approve_result.get("error", "Unknown error")
        if approve_result.get("cleanup_performed"):
            error_msg += " (cleanup performed, please retry)"
        logger.error(f"Failed to approve image: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    
    final_path = approve_result["final_path"]
    
    approval_status = load_approval_status()
    approval_status[image_path] = "approved"
    approval_status[final_path] = "final"
    save_approval_status(approval_status)
    
    current_params = {
        "lora_scale": 0.77,
        "guidance_scale": 2.5,
        "num_inference_steps": 30
    }
    
    await quality_agent.record_feedback(
        influencer_name=inf_config.name,
        influencer_handle=inf_config.handle,
        image_path=image_path,
        prompt="",
        params=current_params,
        approved=True,
        notes="Approved via gallery workflow"
    )
    
    twitter_result = None
    if auto_post and "starbright" in influencer.lower():
        twitter_result = await _auto_post_to_twitter(final_path, "starbright_monroe")
    
    return {
        "status": "approved",
        "image_path": image_path,
        "final_path": final_path,
        "cloud_path": approve_result.get("cloud_path"),
        "influencer": influencer,
        "twitter_post": twitter_result
    }


@router.post("/auto-post")
async def workflow_auto_post(
    image_path: str = Query(..., description="Path to approved image"),
    influencer: str = Query(default="starbright_monroe", description="Influencer ID")
):
    """
    Manually trigger auto-post for an already-approved image.
    Generates caption, hashtags, CTA and posts to X.
    """
    source_path = Path(image_path)
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")
    
    result = await _auto_post_to_twitter(str(source_path), influencer)
    
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.get("/reject")
async def workflow_reject_image(
    image_path: str = Query(..., description="Path to image file"),
    influencer: str = Query(default="Luna Vale", description="Influencer name"),
    notes: Optional[str] = Query(default=None, description="Rejection reason")
):
    logger.info(f"Rejecting image: {image_path}")
    
    inf_config = None
    for inf in INFLUENCERS:
        if inf.name.lower() == influencer.lower():
            inf_config = inf
            break
    
    if not inf_config:
        raise HTTPException(status_code=404, detail=f"Influencer not found: {influencer}")
    
    approval_status = load_approval_status()
    approval_status[image_path] = "rejected"
    save_approval_status(approval_status)
    
    current_params = {
        "lora_scale": 0.77,
        "guidance_scale": 2.5,
        "num_inference_steps": 30
    }
    
    await quality_agent.record_feedback(
        influencer_name=inf_config.name,
        influencer_handle=inf_config.handle,
        image_path=image_path,
        prompt="",
        params=current_params,
        approved=False,
        notes=notes or "Rejected via gallery workflow"
    )
    
    archive_path = None
    try:
        source_path = Path(image_path)
        if source_path.exists():
            handle = inf_config.handle.replace("@", "").lower()
            archive_dir = Path(f"content/archives/{handle}")
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            archive_file = archive_dir / source_path.name
            shutil.move(str(source_path), str(archive_file))
            archive_path = str(archive_file)
            logger.info(f"Archived rejected image to: {archive_path}")
            
            del approval_status[image_path]
            approval_status[archive_path] = "rejected"
            save_approval_status(approval_status)
    except Exception as e:
        logger.warning(f"Failed to archive rejected image: {e}")
    
    return {
        "status": "rejected",
        "image_path": image_path,
        "archive_path": archive_path,
        "influencer": influencer,
        "notes": notes
    }


@router.get("/stats")
async def workflow_stats():
    """Get workflow statistics"""
    approval_status = load_approval_status()
    
    stats = {
        "total": len(approval_status),
        "approved": 0,
        "rejected": 0,
        "final": 0,
        "pending": 0
    }
    
    for path, status in approval_status.items():
        if status in stats:
            stats[status] += 1
        else:
            stats["pending"] += 1
    
    return stats


@router.get("/storage/status")
async def storage_status():
    """Get storage status report with disk usage and directory stats."""
    return storage_manager.get_storage_report()


@router.post("/storage/cleanup")
async def storage_cleanup(dry_run: bool = Query(default=False, description="Preview cleanup without deleting")):
    """
    Run automatic cleanup on all managed directories.
    Keeps newest N images per directory based on retention policy.
    """
    result = storage_manager.run_cleanup(dry_run=dry_run)
    return result


@router.get("/storage/check")
async def storage_check(required_mb: float = Query(default=100.0, description="Required free space in MB")):
    """Check if there's enough disk space for operations."""
    has_space, message = storage_manager.check_disk_space(required_mb)
    return {
        "has_space": has_space,
        "message": message,
        "disk_usage": storage_manager.get_disk_usage()
    }
