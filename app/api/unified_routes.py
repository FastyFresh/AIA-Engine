"""Unified content generation routes."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/unified", tags=["Unified Content"])

from app.agents.unified_content_agent import unified_content_agent, INFLUENCER_CONFIG


class UnifiedGenerateRequest(BaseModel):
    influencer_id: str = "starbright_monroe"
    theme: str = "general"
    outfit: str = "casual outfit"
    time_of_day: Optional[str] = None
    use_background_ref: bool = True
    filename: Optional[str] = None


class UnifiedWeeklyRequest(BaseModel):
    influencer_id: str = "starbright_monroe"
    content_plan: list[dict]
    use_background_ref: bool = True


@router.get("/influencers")
async def unified_list_influencers():
    """List available influencers for unified content generation"""
    influencers = []
    for inf_id, config in INFLUENCER_CONFIG.items():
        influencers.append({
            "id": inf_id,
            "name": config["name"],
            "face_ref": config["face_ref"],
            "body_ref": config["body_ref"],
            "output_dir": config["output_dir"]
        })
    return {"influencers": influencers}


@router.post("/generate")
async def unified_generate_content(request: UnifiedGenerateRequest):
    """
    Generate a single piece of content using the Unified Content Agent.
    
    Uses Seedream4 with dual-reference (face + body) and optional background reference.
    Includes LLM-powered pose/expression selection and theme-appropriate backgrounds.
    """
    if request.influencer_id not in INFLUENCER_CONFIG:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown influencer: {request.influencer_id}. Available: {list(INFLUENCER_CONFIG.keys())}"
        )
    
    try:
        result = await unified_content_agent.generate_content(
            influencer_id=request.influencer_id,
            theme=request.theme,
            outfit=request.outfit,
            time_of_day=request.time_of_day,
            use_background_ref=request.use_background_ref,
            filename=request.filename
        )
        return result
    except Exception as e:
        logger.error(f"Unified generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-weekly")
async def unified_generate_weekly(request: UnifiedWeeklyRequest):
    """
    Generate a week's worth of content using the Unified Content Agent.
    
    Content plan example:
    [
        {"day": "Monday", "theme": "morning_coffee", "outfit": "silk robe"},
        {"day": "Tuesday", "theme": "workout", "outfit": "yoga pants and sports bra"},
        ...
    ]
    """
    if request.influencer_id not in INFLUENCER_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown influencer: {request.influencer_id}"
        )
    
    results = []
    for i, plan in enumerate(request.content_plan):
        try:
            result = await unified_content_agent.generate_content(
                influencer_id=request.influencer_id,
                theme=plan.get("theme", "general"),
                outfit=plan.get("outfit", "casual outfit"),
                time_of_day=plan.get("time_of_day"),
                use_background_ref=request.use_background_ref,
                filename=f"weekly_{i+1}_{plan.get('day', 'day')}"
            )
            results.append({
                "day": plan.get("day", f"Day {i+1}"),
                "status": "success",
                "result": result
            })
        except Exception as e:
            results.append({
                "day": plan.get("day", f"Day {i+1}"),
                "status": "error",
                "error": str(e)
            })
    
    return {
        "influencer_id": request.influencer_id,
        "total": len(results),
        "successful": len([r for r in results if r["status"] == "success"]),
        "results": results
    }


@router.get("/generated")
async def unified_list_generated(
    influencer_id: str = Query(default="starbright_monroe"),
    limit: int = Query(default=20)
):
    """List generated unified content images"""
    if influencer_id not in INFLUENCER_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unknown influencer: {influencer_id}")
    
    output_dir = Path(INFLUENCER_CONFIG[influencer_id]["output_dir"])
    if not output_dir.exists():
        return {"images": [], "count": 0}
    
    images = []
    for f in sorted(output_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
        images.append({
            "filename": f.name,
            "path": str(f),
            "url": f"/api/unified/image/{influencer_id}/{f.name}",
            "size_kb": round(f.stat().st_size / 1024, 1),
            "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    
    return {"images": images, "count": len(images), "influencer_id": influencer_id}


@router.get("/image/{influencer_id}/{filename}")
async def unified_serve_image(influencer_id: str, filename: str):
    """Serve a generated unified content image"""
    if influencer_id not in INFLUENCER_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unknown influencer: {influencer_id}")
    
    file_path = Path(INFLUENCER_CONFIG[influencer_id]["output_dir"]) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        file_path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}
    )
