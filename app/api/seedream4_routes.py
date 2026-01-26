"""Seedream4 image generation routes."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/seedream4", tags=["Seedream4"])

from app.services.seedream4_service import Seedream4Service, CONTENT_PRESETS

seedream4_service = Seedream4Service()


class Seedream4GenerateRequest(BaseModel):
    prompt: str
    scene: str = ""
    outfit: str = ""
    pose: str = "natural relaxed pose"
    aspect_ratio: str = "9:16"
    seed: Optional[int] = None
    filename_prefix: str = "starbright"


class ContentGenerateRequest(BaseModel):
    outfit: str
    scene: str
    lighting: str = "natural lighting"
    accessories: str = "random"
    filename_prefix: str = "starbright"
    count: int = 1


@router.post("/generate")
async def seedream4_generate(request: Seedream4GenerateRequest):
    """Generate image using Seedream4 with face + body reference images"""
    
    if request.prompt:
        prompt = request.prompt
    else:
        prompt = seedream4_service.build_prompt(
            scene=request.scene,
            outfit=request.outfit,
            pose=request.pose
        )
    
    result = await seedream4_service.generate(
        prompt=prompt,
        aspect_ratio=request.aspect_ratio,
        seed=request.seed,
        filename_prefix=request.filename_prefix
    )
    
    return result


@router.get("/generate-quick")
async def seedream4_generate_quick(
    scene: str = Query(default="minimalist modern luxury apartment", description="Scene/setting"),
    outfit: str = Query(default="pink two-piece bikini", description="Outfit description"),
    lighting: str = Query(default="evening interior lighting, warm ambient light", description="Lighting"),
    seed: int = Query(default=None, description="Random seed")
):
    """Quick generate with V3 prompt format (pale ivory skin, slim athletic build)"""
    
    prompt = seedream4_service.build_prompt_simple(
        outfit=outfit,
        scene=scene,
        lighting=lighting
    )
    
    result = await seedream4_service.generate(
        prompt=prompt,
        seed=seed,
        filename_prefix="quick"
    )
    
    return result


@router.post("/content")
async def seedream4_generate_content(request: ContentGenerateRequest):
    """
    Generate content at scale using optimized V3 prompt format
    
    Accessories options:
    - "none": No jewelry/earrings
    - "minimal": Small stud earrings only
    - "earrings": Small hoop earrings
    - "necklace": Delicate necklace, no earrings
    - "random": Randomly varies accessories (default, weighted toward no earrings)
    """
    service = Seedream4Service()
    results = []
    
    for i in range(request.count):
        prefix = f"{request.filename_prefix}_{i+1}" if request.count > 1 else request.filename_prefix
        result = await service.generate_content(
            outfit=request.outfit,
            scene=request.scene,
            lighting=request.lighting,
            accessories=request.accessories,
            filename_prefix=prefix
        )
        results.append(result)
    
    return {
        "status": "success",
        "count": len(results),
        "results": results
    }


@router.get("/presets")
async def seedream4_get_presets():
    """Get available content presets for quick generation"""
    return {"presets": CONTENT_PRESETS}


@router.get("/images")
async def seedream4_list_images(limit: int = Query(default=20)):
    """List generated Seedream4 images"""
    output_dir = Path("content/seedream4_output")
    if not output_dir.exists():
        return {"images": [], "count": 0}
    
    images = []
    for f in sorted(output_dir.glob("*.png"), reverse=True)[:limit]:
        images.append({
            "filename": f.name,
            "path": str(f),
            "url": f"/content/seedream4_output/{f.name}",
            "size_kb": round(f.stat().st_size / 1024, 1),
            "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    
    return {"images": images, "count": len(images)}


@router.post("/face-swap")
async def seedream4_face_swap(
    image_path: str = Query(..., description="Path to generated Seedream4 image")
):
    """Face swap a Seedream4 generated image with Starbright canonical face"""
    from app.agents.face_swap_agent import FaceSwapAgent
    
    swap_agent = FaceSwapAgent()
    
    result = await swap_agent.swap_face(
        target_image_path=image_path,
        influencer_name="Starbright Monroe",
        output_dir="content/seedream4_swapped"
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return {
        "status": "success",
        "original": image_path,
        "swapped": result.get("image_path")
    }
