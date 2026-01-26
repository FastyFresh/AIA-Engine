"""Micro-loop video generation routes"""
import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

from app.pipeline_config import MICRO_MOVEMENT_PROMPTS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/micro_loop", tags=["micro_loop"])


def get_micro_movement_agent():
    from app.agents.micro_movement_agent import MicroMovementAgent
    return MicroMovementAgent()


@router.get("/hero_refs")
async def get_hero_refs(
    influencer: str = Query(..., description="Influencer handle (e.g., luna_vale)")
):
    """Get available hero reference images for micro-loop generation"""
    agent = get_micro_movement_agent()
    refs = await agent.list_hero_refs(influencer)
    return {"hero_refs": refs, "count": len(refs)}


@router.post("/upload_hero")
async def upload_hero_image(
    file: UploadFile = File(...),
    influencer: str = Form(...),
    custom_name: Optional[str] = Form(default=None)
):
    """Upload a hero reference image with automatic LLM-powered labeling."""
    from app.agents.hero_image_analyzer import process_uploaded_hero
    import tempfile
    import shutil
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    if influencer not in ["starbright_monroe", "luna_vale"]:
        raise HTTPException(status_code=400, detail="Invalid influencer. Use 'starbright_monroe' or 'luna_vale'")
    
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name
    
    try:
        result = await process_uploaded_hero(temp_path, influencer, custom_name)
        return result
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze_hero")
async def analyze_hero_image_endpoint(
    file: UploadFile = File(...),
    influencer: str = Form(default="starbright_monroe")
):
    """Analyze a hero image without saving it."""
    from app.agents.hero_image_analyzer import analyze_hero_image
    import tempfile
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        temp_path = tmp.name
    
    try:
        result = await analyze_hero_image(temp_path, influencer)
        return result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/movements")
async def get_available_movements():
    """Get list of available micro-movement types"""
    return {
        "movements": list(MICRO_MOVEMENT_PROMPTS.keys()),
        "prompts": MICRO_MOVEMENT_PROMPTS
    }


@router.post("/generate")
async def generate_micro_loop(
    hero_image_path: str = Query(..., description="Path to the hero reference image"),
    influencer: str = Query(..., description="Influencer handle"),
    movement_type: Optional[str] = Query(default=None, description="Movement type (random if not specified)"),
    custom_prompt: Optional[str] = Query(default=None, description="Custom prompt override"),
    model: Optional[str] = Query(default="kling", description="Model: kling, consisti2v, or svd")
):
    """Generate a micro-movement video from a hero reference image"""
    agent = get_micro_movement_agent()
    logger.info(f"Micro-loop generation: {influencer} / {movement_type} / model: {model}")
    
    result = await agent.generate_loop(
        hero_image_path=hero_image_path,
        influencer_handle=influencer,
        movement_type=movement_type,
        custom_prompt=custom_prompt,
        model=model
    )
    return result


@router.get("/models")
async def get_available_models():
    """Get list of available video generation models"""
    agent = get_micro_movement_agent()
    return agent.get_available_models()


@router.get("/list")
async def list_micro_loops(
    influencer: str = Query(..., description="Influencer handle"),
    limit: int = Query(default=50, description="Max number of loops to return")
):
    """List generated micro-movement videos for an influencer"""
    agent = get_micro_movement_agent()
    loops = await agent.list_loops(influencer, limit)
    return {"loops": loops, "count": len(loops)}


@router.get("/video/{video_path:path}")
async def serve_micro_loop_video(video_path: str):
    """Serve a micro-loop video file"""
    loops_base = Path("content/loops").resolve()
    video_file = (loops_base / video_path).resolve()
    
    if not str(video_file).startswith(str(loops_base)):
        raise HTTPException(status_code=403, detail="Access denied: path traversal detected")
    
    if not video_file.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not video_file.suffix.lower() in [".mp4", ".webm", ".gif"]:
        raise HTTPException(status_code=403, detail="Invalid file type")
    
    return FileResponse(
        video_file,
        media_type="video/mp4",
        headers={"Cache-Control": "no-cache"}
    )


@router.post("/caption")
async def add_caption_to_loop(
    video_path: str = Query(..., description="Path to the video file"),
    caption_lines: str = Query(..., description="Caption text, use | for line breaks"),
    position: str = Query(default="center", description="Position: top, center, bottom"),
    font_size: int = Query(default=24, description="Font size"),
    font_color: str = Query(default="white", description="Font color"),
    outline_color: str = Query(default="black", description="Outline color"),
    outline_width: int = Query(default=2, description="Outline width")
):
    """Add Instagram Reels-style caption overlay to a video"""
    agent = get_micro_movement_agent()
    lines = [line.strip() for line in caption_lines.split("|") if line.strip()]
    
    if not lines:
        return {"success": False, "error": "No caption text provided"}
    
    result = await agent.add_caption_to_video(
        video_path=video_path,
        caption_lines=lines,
        position=position,
        font_size=font_size,
        font_color=font_color,
        outline_color=outline_color,
        outline_width=outline_width
    )
    return result


@router.post("/watermark")
async def add_watermark_to_video(
    video_path: str = Query(..., description="Path to the video file"),
    influencer: str = Query(default="starbright_monroe", description="Influencer name"),
    position: str = Query(default="bottom_right", description="Position")
):
    """Add watermark overlay to a video"""
    agent = get_micro_movement_agent()
    result = await agent.add_watermark(
        video_path=video_path,
        influencer=influencer,
        position=position
    )
    return result


@router.post("/caption_and_watermark")
async def add_caption_and_watermark(
    video_path: str = Query(..., description="Path to the video file"),
    caption_lines: str = Query(..., description="Caption text, use | for line breaks"),
    influencer: str = Query(default="starbright_monroe", description="Influencer name"),
    caption_position: str = Query(default="center", description="Caption position"),
    watermark_position: str = Query(default="bottom_right", description="Watermark position")
):
    """Add both caption overlay and watermark to a video"""
    agent = get_micro_movement_agent()
    lines = [line.strip() for line in caption_lines.split("|") if line.strip()]
    
    if not lines:
        return {"success": False, "error": "No caption text provided"}
    
    result = await agent.add_caption_and_watermark(
        video_path=video_path,
        caption_lines=lines,
        influencer=influencer,
        caption_position=caption_position,
        watermark_position=watermark_position
    )
    return result


@router.get("/captioned")
async def list_captioned_loops(
    influencer: Optional[str] = Query(default=None, description="Influencer handle"),
    limit: int = Query(default=50, description="Max number of videos to return")
):
    """List captioned videos"""
    agent = get_micro_movement_agent()
    videos = await agent.list_captioned_videos(influencer, limit)
    return {"videos": videos, "count": len(videos)}


@router.get("/caption_suggestions")
async def get_caption_suggestions(
    count: int = Query(default=5, description="Number of suggestions"),
    theme: Optional[str] = Query(default=None, description="Filter by theme"),
    influencer: Optional[str] = Query(default="luna_vale", description="Influencer")
):
    """Get random caption suggestions (template-based fallback)"""
    from app.caption_templates import (
        get_random_captions, 
        get_captions_by_theme, 
        get_all_themes,
        format_caption_for_display
    )
    
    influencer_key = influencer.lower().replace("@", "").replace(" ", "_") if influencer else "luna_vale"
    
    if theme:
        captions = get_captions_by_theme(theme, influencer_key)
        if len(captions) > count:
            import random
            captions = random.sample(captions, count)
    else:
        captions = get_random_captions(count, influencer_key)
    
    suggestions = []
    for cap in captions:
        suggestions.append({
            "id": cap["id"],
            "lines": cap["lines"],
            "theme": cap["theme"],
            "formatted": format_caption_for_display(cap),
            "influencer": influencer_key
        })
    
    return {
        "suggestions": suggestions,
        "themes": get_all_themes(influencer_key),
        "count": len(suggestions),
        "influencer": influencer_key
    }


@router.get("/generate_caption")
async def generate_ai_caption(
    hero_image: Optional[str] = Query(default=None, description="Hero image filename"),
    movement_type: Optional[str] = Query(default=None, description="Movement type"),
    count: int = Query(default=5, description="Number of captions"),
    influencer: Optional[str] = Query(default="luna_vale", description="Influencer")
):
    """Generate AI-powered captions using XAI/Grok"""
    influencer_key = influencer.lower().replace("@", "").replace(" ", "_") if influencer else "luna_vale"
    
    if influencer_key == "starbright_monroe" or influencer_key == "starbright":
        from app.agents.starbright_caption_generator import starbright_caption_generator
        caption_generator = starbright_caption_generator
        persona_name = "Starbright Monroe"
    else:
        from app.agents.luna_caption_generator import luna_caption_generator
        caption_generator = luna_caption_generator
        persona_name = "Luna Vale"
    
    logger.info(f"Generating {count} AI captions for {persona_name}")
    
    captions = await caption_generator.generate_multiple(
        count=count,
        hero_image_filename=hero_image,
        movement_type=movement_type
    )
    
    suggestions = []
    for i, cap in enumerate(captions):
        suggestions.append({
            "id": f"ai_{i}_{cap.get('pattern', 'X')}",
            "lines": cap.get("lines", []),
            "pattern": cap.get("pattern", "?"),
            "emotional_mode": cap.get("emotional_mode", ""),
            "formatted": cap.get("caption", ""),
            "source": cap.get("source", "unknown"),
            "context": cap.get("context", {}),
            "influencer": influencer_key
        })
    
    return {
        "suggestions": suggestions,
        "count": len(suggestions),
        "source": "ai_generated" if suggestions and suggestions[0].get("source") == "ai_generated" else "template_fallback",
        "influencer": influencer_key,
        "persona": persona_name
    }


@router.get("/luna/modules")
async def get_luna_modules():
    """Get Luna's modular prompt options (outfits, backgrounds, vibes)"""
    from app.services.prompt_builder import get_luna_prompt_builder
    
    builder = get_luna_prompt_builder()
    if not builder:
        raise HTTPException(status_code=404, detail="Luna config not found")
    
    return {
        "outfits": builder.list_all_outfits(),
        "backgrounds": builder.list_all_backgrounds(),
        "vibes": builder.list_all_vibes(),
        "camera_lighting": builder.get_camera_lighting(),
        "face_ref": builder.face_ref,
        "body_ref": builder.body_ref,
        "negative_prompt": builder.negative_prompt
    }


@router.post("/luna/assemble_prompt")
async def assemble_luna_prompt(
    outfit: Optional[str] = Form(default=None),
    background: Optional[str] = Form(default=None),
    vibe: Optional[str] = Form(default=None),
    outfit_tier: int = Form(default=1),
    background_category: str = Form(default="safe_high_reach"),
    vibe_category: str = Form(default="core")
):
    """Assemble a Luna prompt from modular blocks"""
    from app.services.prompt_builder import get_luna_prompt_builder
    
    builder = get_luna_prompt_builder()
    if not builder:
        raise HTTPException(status_code=404, detail="Luna config not found")
    
    prompt, negative = builder.assemble_prompt(
        outfit=outfit,
        background=background,
        vibe=vibe,
        outfit_tier=outfit_tier,
        background_category=background_category,
        vibe_category=vibe_category
    )
    
    return {
        "positive_prompt": prompt,
        "negative_prompt": negative,
        "modules_used": {
            "outfit": outfit or f"sampled from tier_{outfit_tier}",
            "background": background or f"sampled from {background_category}",
            "vibe": vibe or f"sampled from {vibe_category}"
        }
    }


@router.post("/luna/generate_batch")
async def generate_luna_modular_batch(
    count: int = Form(default=5, ge=1, le=8),
    outfit_tier: int = Form(default=1, ge=1, le=3),
    fixed_outfit: Optional[str] = Form(default=None),
    background_category: str = Form(default="safe_high_reach"),
    vibe_category: str = Form(default="core")
):
    """Generate a batch of Luna images using the modular prompt system"""
    from app.services.prompt_builder import get_luna_prompt_builder
    from app.services.fal_seedream_service import FalSeedreamService
    
    builder = get_luna_prompt_builder()
    if not builder:
        raise HTTPException(status_code=404, detail="Luna config not found")
    
    prompts = builder.generate_batch_prompts(
        count=count,
        outfit_tier=outfit_tier,
        fixed_outfit=fixed_outfit,
        background_category=background_category,
        vibe_category=vibe_category
    )
    
    fal_service = FalSeedreamService(influencer_id="luna_vale")
    
    results = []
    for i, (prompt, negative) in enumerate(prompts):
        logger.info(f"Generating Luna image {i+1}/{count}")
        try:
            image_path = await fal_service.generate_with_references(
                prompt=prompt,
                negative_prompt=negative
            )
            results.append({
                "index": i,
                "success": True,
                "image_path": image_path,
                "prompt_preview": prompt[:200] + "..."
            })
        except Exception as e:
            logger.error(f"Failed to generate image {i+1}: {e}")
            results.append({
                "index": i,
                "success": False,
                "error": str(e)
            })
    
    successful = [r for r in results if r.get("success")]
    return {
        "batch_id": f"luna_batch_{int(__import__('time').time())}",
        "total_requested": count,
        "successful": len(successful),
        "failed": count - len(successful),
        "results": results,
        "outfit_used": fixed_outfit or f"sampled from tier_{outfit_tier}",
        "background_category": background_category,
        "vibe_category": vibe_category
    }
