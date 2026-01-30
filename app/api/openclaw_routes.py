"""
OpenClaw Webhook Integration Routes
Allows OpenClaw to request content generation from AIA Engine
"""

from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import json
import logging
import secrets
import hashlib
import hmac

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/openclaw", tags=["openclaw"])

OPENCLAW_WEBHOOK_SECRET = os.getenv("OPENCLAW_WEBHOOK_SECRET", "")

def verify_webhook_token(authorization: str = Header(None), x_openclaw_token: str = Header(None)) -> bool:
    if not OPENCLAW_WEBHOOK_SECRET:
        return True
    
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif x_openclaw_token:
        token = x_openclaw_token
    
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    if not hmac.compare_digest(token, OPENCLAW_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return True


class ContentRequest(BaseModel):
    influencer: str = "starbright_monroe"
    content_type: str = "image"
    prompt: Optional[str] = None
    style: Optional[str] = None
    callback_url: Optional[str] = None


class LipSyncRequest(BaseModel):
    influencer: str = "starbright_monroe"
    hero_image_path: Optional[str] = None
    audio_url: Optional[str] = None
    audio_path: Optional[str] = None
    prompt: Optional[str] = None
    callback_url: Optional[str] = None


class CaptionRequest(BaseModel):
    influencer: str = "starbright_monroe"
    context: Optional[str] = None
    mood: Optional[str] = None
    platform: str = "instagram"
    count: int = 3


class PostRequest(BaseModel):
    influencer: str = "starbright_monroe"
    platform: str
    content_path: str
    caption: str
    callback_url: Optional[str] = None


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AIA Engine",
        "version": "1.2.0",
        "openclaw_integration": True,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/capabilities")
async def get_capabilities():
    return {
        "influencers": ["starbright_monroe", "luna_vale"],
        "content_types": ["image", "video", "lipsync", "caption"],
        "platforms": ["twitter", "telegram", "instagram", "tiktok"],
        "endpoints": {
            "generate_image": "/api/openclaw/generate/image",
            "generate_lipsync": "/api/openclaw/generate/lipsync",
            "generate_caption": "/api/openclaw/generate/caption",
            "list_content": "/api/openclaw/content/list",
            "get_hero_images": "/api/openclaw/content/heroes"
        }
    }


@router.get("/content/list")
async def list_available_content(
    influencer: str = Query("starbright_monroe"),
    content_type: str = Query("all"),
    limit: int = Query(20)
):
    from pathlib import Path
    
    base_path = Path(f"content/final/{influencer}")
    videos_path = Path("content/videos/omnihuman")
    
    content = {
        "images": [],
        "videos": [],
        "lipsync": []
    }
    
    if base_path.exists() and content_type in ["all", "images"]:
        for f in sorted(base_path.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            content["images"].append({
                "filename": f.name,
                "path": str(f),
                "size_mb": f.stat().st_size / (1024 * 1024),
                "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    
    if videos_path.exists() and content_type in ["all", "lipsync"]:
        for f in sorted(videos_path.glob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            content["lipsync"].append({
                "filename": f.name,
                "path": str(f),
                "size_mb": f.stat().st_size / (1024 * 1024),
                "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    
    return {
        "influencer": influencer,
        "content": content,
        "total": sum(len(v) for v in content.values())
    }


@router.get("/content/heroes")
async def get_hero_images(
    influencer: str = Query("starbright_monroe"),
    limit: int = Query(10)
):
    from pathlib import Path
    
    base_path = Path(f"content/final/{influencer}")
    heroes = []
    
    if base_path.exists():
        for f in sorted(base_path.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            heroes.append({
                "filename": f.name,
                "path": str(f),
                "size_mb": f.stat().st_size / (1024 * 1024),
                "url": f"/gallery/image/{f}"
            })
    
    return {
        "influencer": influencer,
        "heroes": heroes,
        "count": len(heroes)
    }


@router.post("/generate/caption")
async def generate_caption(request: CaptionRequest):
    from app.services.venice_service import VeniceService
    
    venice = VeniceService()
    
    platform_styles = {
        "instagram": "Instagram caption with emojis, engaging hooks, and relevant hashtags",
        "tiktok": "TikTok caption - short, trendy, with viral hooks",
        "twitter": "Twitter post - concise, witty, under 280 chars",
        "telegram": "Telegram message - personal, direct, with call to action"
    }
    
    style = platform_styles.get(request.platform, platform_styles["instagram"])
    
    prompt = f"""Generate {request.count} unique {style} for an AI influencer named Starbright Monroe.

Starbright is a flirty, playful 21-year-old digital creator. She's confident, teasing, and connects deeply with her fans.

Context: {request.context or 'General engaging content'}
Mood: {request.mood or 'playful and flirty'}

Return ONLY a JSON array of {request.count} captions, no other text."""
    
    try:
        response = await venice.generate_text(prompt)
        captions = json.loads(response) if isinstance(response, str) else response
        
        return {
            "success": True,
            "influencer": request.influencer,
            "platform": request.platform,
            "captions": captions
        }
    except Exception as e:
        logger.error(f"Caption generation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/generate/lipsync")
async def generate_lipsync(request: LipSyncRequest, background_tasks: BackgroundTasks):
    import fal_client
    import httpx
    from pathlib import Path
    import subprocess
    
    try:
        if request.hero_image_path:
            image_path = request.hero_image_path
        else:
            base_path = Path(f"content/final/{request.influencer}")
            if base_path.exists():
                images = sorted(base_path.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
                if images:
                    image_path = str(images[0])
                else:
                    raise HTTPException(status_code=404, detail="No hero images found")
            else:
                raise HTTPException(status_code=404, detail="Influencer content not found")
        
        file_size = Path(image_path).stat().st_size
        if file_size > 5 * 1024 * 1024:
            resized = '/tmp/resized_hero_openclaw.jpg'
            subprocess.run(['magick', image_path, '-resize', '1280x1280>', '-quality', '85', resized], check=True)
            image_path = resized
        
        image_url = fal_client.upload_file(image_path)
        
        if request.audio_url:
            audio_url = request.audio_url
        elif request.audio_path:
            audio_url = fal_client.upload_file(request.audio_path)
        else:
            raise HTTPException(status_code=400, detail="Either audio_url or audio_path required")
        
        prompt = request.prompt or "Natural lip sync, realistic mouth movements, subtle expressions, maintain natural mouth size"
        
        result = fal_client.subscribe(
            'fal-ai/kling-video/ai-avatar/v2/pro',
            arguments={
                'image_url': image_url,
                'audio_url': audio_url,
                'prompt': prompt
            }
        )
        
        video_url = result.get('video', {}).get('url')
        
        if video_url:
            resp = httpx.get(video_url, timeout=60.0)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"content/videos/omnihuman/{request.influencer}_lipsync_{timestamp}.mp4")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(resp.content)
            
            return {
                "success": True,
                "video_path": str(output_path),
                "video_url": f"/gallery/video/{output_path}",
                "size_mb": len(resp.content) / (1024 * 1024)
            }
        else:
            return {"success": False, "error": "No video URL in response"}
            
    except Exception as e:
        logger.error(f"Lip-sync generation failed: {e}")
        return {"success": False, "error": str(e)}


@router.post("/generate/image")
async def generate_image(request: ContentRequest):
    from app.services.seedream_service import SEEDreamService
    
    try:
        seedream = SEEDreamService()
        
        prompt = request.prompt or f"Professional photo of Starbright Monroe, a beautiful young woman with pale porcelain skin, dark brown hair, olive-brown eyes, subtle freckles, petite frame"
        
        if request.style:
            prompt += f", {request.style}"
        
        result = await seedream.generate_image(prompt, influencer=request.influencer)
        
        return {
            "success": True,
            "image_path": result.get("output_path"),
            "image_url": f"/gallery/image/{result.get('output_path')}"
        }
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/webhook/info")
async def webhook_info():
    return {
        "name": "AIA Engine OpenClaw Integration",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/openclaw/generate/lipsync": "Generate lip-sync video from hero image + audio",
            "POST /api/openclaw/generate/caption": "Generate captions for social platforms",
            "POST /api/openclaw/generate/image": "Generate new influencer images",
            "GET /api/openclaw/content/list": "List available content",
            "GET /api/openclaw/content/heroes": "Get hero images for lip-sync",
            "GET /api/openclaw/health": "Health check",
            "GET /api/openclaw/capabilities": "List all capabilities"
        },
        "authentication": "Bearer token via Authorization header or x-openclaw-token header",
        "callback_support": True
    }
