"""Telegram bot API routes (admin-only endpoints)"""
import os
from pathlib import Path

from fastapi import APIRouter, Header, Depends
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/telegram", tags=["telegram"])

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")
ALLOWED_CONTENT_DIRS = ["content/final", "content/teasers", "content/generated", "content/telegram"]


def verify_admin_key(x_admin_key: str = Header(None), x_api_key: str = Header(None)):
    """Verify admin API key for protected endpoints"""
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=503, detail="Admin API not configured")
    api_key = x_admin_key or x_api_key
    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return True


def validate_content_path(path: str) -> bool:
    """Ensure path is within allowed content directories"""
    resolved = Path(path).resolve()
    for allowed_dir in ALLOWED_CONTENT_DIRS:
        allowed_resolved = Path(allowed_dir).resolve()
        try:
            resolved.relative_to(allowed_resolved)
            return True
        except ValueError:
            continue
    return False


class ContentDropRequest(BaseModel):
    persona_id: str
    content_path: str
    caption: str
    tier: str = "companion"
    content_type: str = "photo"


class GenerateCaptionRequest(BaseModel):
    persona_id: str = "starbright_monroe"
    context: str = ""
    mood: str = "flirty"


@router.get("/stats")
async def get_telegram_stats(authorized: bool = Depends(verify_admin_key)):
    """Get stats for all Telegram bots (admin only)"""
    from app.telegram.user_database import db as telegram_db
    
    await telegram_db.init_db()
    
    stats = {}
    for persona_id in ["starbright_monroe", "luna_vale"]:
        persona_stats = await telegram_db.get_user_stats(persona_id)
        stats[persona_id] = persona_stats
    
    return {
        "starbright": stats.get("starbright_monroe", {}),
        "luna": stats.get("luna_vale", {}),
        "total_users": sum(s.get("total_users", 0) for s in stats.values()),
        "total_paying": sum(
            s.get("companion_users", 0) + s.get("vip_users", 0) 
            for s in stats.values()
        )
    }


@router.post("/run-onboarding")
async def run_onboarding_jobs(authorized: bool = Depends(verify_admin_key)):
    """Run onboarding drip messages for all personas (admin only)"""
    from app.telegram.content_service import ContentService
    from app.telegram.user_database import db as telegram_db
    
    await telegram_db.init_db()
    
    results = {}
    for persona_id in ["starbright_monroe", "luna_vale"]:
        service = ContentService(persona_id)
        persona_results = {}
        for day in [0, 3, 7]:
            count = await service.send_onboarding_messages(day)
            persona_results[f"day_{day}"] = count
        results[persona_id] = persona_results
    
    return {"status": "completed", "messages_sent": results}


@router.post("/send-content-drop")
async def send_content_drop(
    request: ContentDropRequest,
    authorized: bool = Depends(verify_admin_key)
):
    """Send exclusive content to subscribers of a persona (admin only)"""
    from app.telegram.content_service import ContentService
    
    if request.persona_id not in ["starbright_monroe", "luna_vale"]:
        raise HTTPException(status_code=400, detail="Invalid persona")
    
    if not validate_content_path(request.content_path):
        raise HTTPException(status_code=403, detail="Content path not allowed")
    
    if not Path(request.content_path).exists():
        raise HTTPException(status_code=404, detail="Content file not found")
    
    service = ContentService(request.persona_id)
    sent_count = await service.send_content_drop(request.content_path, request.caption, request.tier, request.content_type)
    
    return {"status": "sent", "recipients": sent_count, "persona": request.persona_id}


@router.post("/send-teaser")
async def send_teaser_content(
    persona_id: str,
    teaser_path: str,
    caption: str,
    authorized: bool = Depends(verify_admin_key)
):
    """Send teaser content to free users (admin only)"""
    from app.telegram.content_service import ContentService
    
    if persona_id not in ["starbright_monroe", "luna_vale"]:
        raise HTTPException(status_code=400, detail="Invalid persona")
    
    if not validate_content_path(teaser_path):
        raise HTTPException(status_code=403, detail="Content path not allowed")
    
    if not Path(teaser_path).exists():
        raise HTTPException(status_code=404, detail="Teaser file not found")
    
    service = ContentService(persona_id)
    sent_count = await service.send_teaser_content(teaser_path, caption)
    
    return {"status": "sent", "recipients": sent_count, "persona": persona_id}


@router.post("/generate-caption")
async def generate_caption(
    request: GenerateCaptionRequest,
    authorized: bool = Depends(verify_admin_key)
):
    """Generate a caption for content using the persona's voice"""
    from app.telegram.conversation_engine import ConversationEngine
    
    if request.persona_id not in ["starbright_monroe", "luna_vale"]:
        raise HTTPException(status_code=400, detail="Invalid persona")
    
    engine = ConversationEngine(request.persona_id)
    
    prompt = f"Generate a short, engaging caption for a photo post. Context: {request.context}. Mood: {request.mood}. Keep it under 100 characters and stay in character."
    
    caption = await engine.generate_response(
        user_message=prompt,
        conversation_history=[],
        user_name="Admin",
        subscription_tier="vip"
    )
    
    return {"caption": caption, "persona": request.persona_id}
