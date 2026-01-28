"""
Venice AI API Routes

Endpoints for Venice image generation with less restrictive content moderation.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from app.services.venice_image_service import venice_image_service

router = APIRouter(prefix="/api/venice", tags=["venice"])


class VeniceGenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = "fluently-xl"
    negative_prompt: Optional[str] = None
    width: int = 1024
    height: int = 1024
    cfg_scale: float = 7.5
    seed: Optional[int] = None
    style_preset: Optional[str] = None
    variants: int = 1
    filename_prefix: str = "venice"


class VeniceStarbrightRequest(BaseModel):
    outfit: str
    scene: str
    pose: str = "standing casually"
    model: str = "fluently-xl"
    width: int = 1024
    height: int = 1360
    seed: Optional[int] = None
    filename_prefix: str = "starbright_venice"


@router.post("/generate")
async def venice_generate(request: VeniceGenerateRequest):
    """Generate image using Venice AI"""
    
    result = await venice_image_service.generate(
        prompt=request.prompt,
        model=request.model,
        negative_prompt=request.negative_prompt,
        width=request.width,
        height=request.height,
        cfg_scale=request.cfg_scale,
        seed=request.seed,
        style_preset=request.style_preset,
        variants=request.variants,
        filename_prefix=request.filename_prefix
    )
    
    return result


@router.post("/generate-starbright")
async def venice_generate_starbright(request: VeniceStarbrightRequest):
    """Generate Starbright Monroe image using Venice AI"""
    
    result = await venice_image_service.generate_starbright(
        outfit=request.outfit,
        scene=request.scene,
        pose=request.pose,
        model=request.model,
        width=request.width,
        height=request.height,
        seed=request.seed,
        filename_prefix=request.filename_prefix
    )
    
    return result


@router.get("/models")
async def venice_list_models():
    """List available Venice image models"""
    return await venice_image_service.list_models()


@router.get("/styles")
async def venice_list_styles():
    """List available Venice style presets"""
    return await venice_image_service.list_styles()


@router.get("/generate-quick")
async def venice_generate_quick(
    prompt: str = Query(..., description="Image prompt"),
    model: str = Query(default="fluently-xl", description="Model to use"),
    width: int = Query(default=1024, description="Width"),
    height: int = Query(default=1360, description="Height"),
    seed: Optional[int] = Query(default=None, description="Seed")
):
    """Quick generate with Venice AI"""
    
    result = await venice_image_service.generate(
        prompt=prompt,
        model=model,
        width=width,
        height=height,
        seed=seed,
        filename_prefix="venice_quick"
    )
    
    return result
