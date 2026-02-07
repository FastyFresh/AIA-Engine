"""
OpenClaw Webhook Integration Routes
Allows OpenClaw VPS to request content generation from AIA Engine
Security: Uses HMAC-safe token comparison via environment secrets
"""

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import json
import logging
import hmac
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/openclaw", tags=["openclaw"])


def verify_webhook_token(authorization: str = Header(None), x_openclaw_token: str = Header(None)) -> bool:
    webhook_secret = os.getenv("OPENCLAW_WEBHOOK_TOKEN", "")
    aia_engine_key = os.getenv("AIA_ENGINE_API_KEY", "")

    if not webhook_secret and not aia_engine_key:
        raise HTTPException(status_code=500, detail="No authentication tokens configured")

    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif x_openclaw_token:
        token = x_openclaw_token

    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    if webhook_secret and hmac.compare_digest(token, webhook_secret):
        return True
    if aia_engine_key and hmac.compare_digest(token, aia_engine_key):
        return True

    raise HTTPException(status_code=401, detail="Invalid token")


OPENCLAW_VPS_IP = os.getenv("OPENCLAW_VPS_IP", "45.32.219.67")
OPENCLAW_VPS_PORT = int(os.getenv("OPENCLAW_VPS_PORT", "18789"))


class ContentRequest(BaseModel):
    influencer: str = "starbright_monroe"
    content_type: str = "image"
    prompt: Optional[str] = None
    style: Optional[str] = None
    callback_url: Optional[str] = None


class CaptionRequest(BaseModel):
    influencer: str = "starbright_monroe"
    context: Optional[str] = None
    mood: Optional[str] = None
    platform: str = "instagram"
    count: int = 3


class AgentRequest(BaseModel):
    message: str
    name: str = "AIA"
    deliver: bool = True


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AIA Engine",
        "version": "1.3.0",
        "openclaw_integration": True,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/capabilities")
async def get_capabilities():
    return {
        "influencers": ["starbright_monroe", "luna_vale"],
        "content_types": ["image", "video", "caption"],
        "platforms": ["twitter", "instagram", "tiktok", "dfans"],
        "endpoints": {
            "generate_image": "POST /api/openclaw/generate/image",
            "generate_caption": "POST /api/openclaw/generate/caption",
            "list_content": "GET /api/openclaw/content/list",
            "get_hero_images": "GET /api/openclaw/content/heroes",
            "vps_status": "GET /api/openclaw/vps/status",
            "send_agent_task": "POST /api/openclaw/vps/agent"
        }
    }


@router.get("/content/list")
async def list_content(
    influencer: str = "starbright_monroe",
    content_type: str = "image",
    limit: int = 20,
    authorization: str = Header(None),
    x_openclaw_token: str = Header(None)
):
    verify_webhook_token(authorization, x_openclaw_token)

    from pathlib import Path
    content_dir = Path("content/seedream4_output")
    if not content_dir.exists():
        return {"files": [], "count": 0}

    files = sorted(content_dir.glob(f"starbright_*.png"), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]

    return {
        "files": [
            {
                "filename": f.name,
                "path": str(f),
                "size_kb": round(f.stat().st_size / 1024, 1),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in files
        ],
        "count": len(files)
    }


@router.get("/content/heroes")
async def get_hero_images(
    influencer: str = "starbright_monroe",
    limit: int = 10,
    authorization: str = Header(None),
    x_openclaw_token: str = Header(None)
):
    verify_webhook_token(authorization, x_openclaw_token)

    from pathlib import Path
    final_dir = Path(f"content/final/{influencer}")
    seedream_dir = Path("content/seedream4_output")

    heroes = []
    for d in [final_dir, seedream_dir]:
        if d.exists():
            for f in sorted(d.glob("*.png"), key=lambda f: f.stat().st_mtime, reverse=True):
                heroes.append({
                    "filename": f.name,
                    "path": str(f),
                    "size_kb": round(f.stat().st_size / 1024, 1),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
                if len(heroes) >= limit:
                    break
        if len(heroes) >= limit:
            break

    return {"heroes": heroes, "count": len(heroes)}


@router.post("/generate/image")
async def generate_image(
    request: ContentRequest,
    authorization: str = Header(None),
    x_openclaw_token: str = Header(None)
):
    verify_webhook_token(authorization, x_openclaw_token)

    try:
        from app.services.fal_seedream_service import FalSeedreamService

        prompt = request.prompt or "Professional photo of Starbright Monroe, very pale porcelain ivory white skin, straight sleek dark brown hair, warm olive-brown eyes, natural freckles across nose and cheeks, extremely thin slender petite body, small natural A-cup breasts, natural skin texture with visible pores, 8K ultra detailed, cinematic lighting"
        if request.style:
            prompt += f", {request.style}"

        service = FalSeedreamService()
        result = await service.generate(
            prompt=prompt,
            influencer=request.influencer
        )

        return {
            "success": True,
            "image_path": result.get("output_path"),
            "prompt": prompt,
            "influencer": request.influencer
        }
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return {"success": False, "error": str(e)}


@router.post("/generate/caption")
async def generate_caption(
    request: CaptionRequest,
    authorization: str = Header(None),
    x_openclaw_token: str = Header(None)
):
    verify_webhook_token(authorization, x_openclaw_token)

    try:
        from app.tools.llm_client import LLMClient

        llm = LLMClient()
        persona_name = "Starbright Monroe" if request.influencer == "starbright_monroe" else "Luna Vale"
        mood_str = f" Mood: {request.mood}." if request.mood else ""
        context_str = f" Context: {request.context}." if request.context else ""

        prompt = f"Generate {request.count} unique, engaging social media captions for {persona_name} on {request.platform}.{mood_str}{context_str} Each caption should be flirty, fun, and include relevant hashtags. Do NOT use any AI-related hashtags. Return only the captions, numbered 1-{request.count}."

        response = await llm.generate(prompt)
        captions = [line.strip() for line in response.strip().split("\n") if line.strip() and line.strip()[0].isdigit()]
        captions = [c.lstrip("0123456789.)- ") for c in captions][:request.count]

        return {
            "success": True,
            "influencer": request.influencer,
            "platform": request.platform,
            "captions": captions if captions else [response.strip()],
            "count": len(captions) if captions else 1
        }
    except Exception as e:
        logger.error(f"Caption generation failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/vps/status")
async def vps_status(
    authorization: str = Header(None),
    x_openclaw_token: str = Header(None)
):
    verify_webhook_token(authorization, x_openclaw_token)

    webhook_token = os.getenv("OPENCLAW_WEBHOOK_TOKEN", "")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"http://{OPENCLAW_VPS_IP}:{OPENCLAW_VPS_PORT}/hooks/wake",
                headers={
                    "Authorization": f"Bearer {webhook_token}",
                    "Content-Type": "application/json"
                },
                json={"text": "status check"}
            )
            return {
                "vps_online": True,
                "status_code": resp.status_code,
                "response": resp.json() if resp.status_code == 200 else resp.text,
                "ip": OPENCLAW_VPS_IP,
                "port": OPENCLAW_VPS_PORT,
                "checked_at": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "vps_online": False,
            "error": str(e),
            "ip": OPENCLAW_VPS_IP,
            "port": OPENCLAW_VPS_PORT,
            "checked_at": datetime.now().isoformat()
        }


@router.post("/vps/agent")
async def send_agent_task(
    request: AgentRequest,
    authorization: str = Header(None),
    x_openclaw_token: str = Header(None)
):
    verify_webhook_token(authorization, x_openclaw_token)

    webhook_token = os.getenv("OPENCLAW_WEBHOOK_TOKEN", "")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"http://{OPENCLAW_VPS_IP}:{OPENCLAW_VPS_PORT}/hooks/agent",
                headers={
                    "Authorization": f"Bearer {webhook_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "message": request.message,
                    "name": request.name,
                    "deliver": request.deliver
                }
            )
            return {
                "success": resp.status_code == 200,
                "status_code": resp.status_code,
                "response": resp.json() if resp.status_code == 200 else resp.text,
                "sent_at": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Failed to send task to OpenClaw VPS: {e}")
        return {"success": False, "error": str(e)}


@router.get("/webhook/info")
async def webhook_info():
    return {
        "name": "AIA Engine OpenClaw Integration",
        "version": "1.3.0",
        "endpoints": {
            "POST /api/openclaw/generate/image": "Generate new influencer images",
            "POST /api/openclaw/generate/caption": "Generate captions for social platforms",
            "GET /api/openclaw/content/list": "List available content",
            "GET /api/openclaw/content/heroes": "Get hero images",
            "GET /api/openclaw/vps/status": "Check OpenClaw VPS status",
            "POST /api/openclaw/vps/agent": "Send task to OpenClaw agent on VPS",
            "GET /api/openclaw/health": "Health check",
            "GET /api/openclaw/capabilities": "List all capabilities"
        },
        "authentication": "Bearer token via Authorization header or x-openclaw-token header",
        "security": {
            "token_comparison": "HMAC-safe constant-time comparison",
            "credentials": "Environment secrets only, never hardcoded"
        }
    }
