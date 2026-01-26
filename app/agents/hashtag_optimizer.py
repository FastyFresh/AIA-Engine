"""
Dynamic Hashtag Optimization Service
Uses XAI/Grok to generate context-aware hashtags optimized for maximum reach.
"""

import os
import random
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


XAI_API_KEY = os.environ.get("XAI_API_KEY")
XAI_BASE_URL = "https://api.x.ai/v1"

FORBIDDEN_HASHTAGS = [
    "ai", "aimodel", "aigirl", "aibeauty", "aiart", "aigenerated",
    "artificialintelligence", "aiinfluencer", "virtualmodel", "digitalmodel",
    "synthetic", "computergenerated", "machinelearning", "deepfake"
]

PERSONA_CONFIG = {
    "starbright_monroe": {
        "name": "Starbright",
        "brand_tags": ["#Starbright", "#Fanvue"],
        "audience": "men ages 20-60",
        "style": "confident, warm, flirty brunette model",
        "content_type": "lifestyle/glamour photos and videos"
    },
    "luna_vale": {
        "name": "Luna",
        "brand_tags": ["#LunaVale", "#Fanvue"],
        "audience": "men ages 20-40",
        "style": "petite, playful, natural beauty",
        "content_type": "lifestyle/glamour photos and videos"
    }
}

EVERGREEN_POOLS = {
    "starbright_monroe": {
        "reach": ["#model", "#bikini", "#beauty", "#gorgeous", "#brunette", "#beach", "#summer", "#hot", "#lifestyle", "#fitness"],
        "engagement": ["#goodmorning", "#weekendvibes", "#selfie", "#ootd", "#vibes", "#mood", "#blessed", "#love"],
        "niche": ["#bikinigirl", "#beachbabe", "#sundayfunday", "#poolside", "#tropical", "#vacation", "#tanned", "#curves"]
    },
    "luna_vale": {
        "reach": ["#model", "#bikini", "#petite", "#cute", "#natural", "#beach", "#summer", "#pretty", "#lifestyle"],
        "engagement": ["#goodmorning", "#weekendvibes", "#selfie", "#ootd", "#vibes", "#mood"],
        "niche": ["#bikinigirl", "#beachbabe", "#sundayfunday", "#poolside", "#petitefashion"]
    }
}

_trending_cache: Dict[str, Any] = {
    "data": None,
    "expires": None
}


def _is_forbidden(tag: str) -> bool:
    """Check if a hashtag contains forbidden AI-related terms"""
    clean_tag = tag.lower().replace("#", "").replace("_", "").replace("-", "")
    return any(forbidden in clean_tag for forbidden in FORBIDDEN_HASHTAGS)


def _filter_forbidden(tags: List[str]) -> List[str]:
    """Remove any hashtags that contain forbidden terms"""
    return [tag for tag in tags if not _is_forbidden(tag)]


def _extract_context_from_filename(filename: str) -> Dict[str, str]:
    """Extract outfit and setting context from video/image filename"""
    filename_lower = filename.lower()
    
    outfit = "casual"
    if "bikini" in filename_lower:
        outfit = "bikini"
    elif "shorts" in filename_lower:
        outfit = "shorts"
    elif "dress" in filename_lower:
        outfit = "dress"
    elif "yoga" in filename_lower or "fitness" in filename_lower:
        outfit = "fitness wear"
    elif "lingerie" in filename_lower:
        outfit = "lingerie"
    
    setting = "studio"
    if "beach" in filename_lower or "ocean" in filename_lower:
        setting = "beach"
    elif "pool" in filename_lower:
        setting = "poolside"
    elif "outdoor" in filename_lower or "nature" in filename_lower:
        setting = "outdoor/nature"
    elif "bedroom" in filename_lower:
        setting = "bedroom"
    elif "gym" in filename_lower:
        setting = "gym"
    
    return {"outfit": outfit, "setting": setting}


def _get_time_context() -> Dict[str, Any]:
    """Get time-based context for hashtag relevance"""
    now = datetime.now()
    hour = now.hour
    weekday = now.strftime("%A")
    
    if 5 <= hour < 12:
        time_of_day = "morning"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
    elif 17 <= hour < 21:
        time_of_day = "evening"
    else:
        time_of_day = "night"
    
    is_weekend = weekday in ["Saturday", "Sunday"]
    
    return {
        "time_of_day": time_of_day,
        "weekday": weekday,
        "is_weekend": is_weekend
    }


async def generate_hashtags_with_grok(
    caption: str,
    influencer: str = "starbright_monroe",
    media_filename: Optional[str] = None,
    max_tags: int = 5
) -> Dict[str, Any]:
    """
    Generate optimized hashtags using XAI/Grok LLM.
    
    Args:
        caption: The caption text being posted
        influencer: Influencer persona name
        media_filename: Optional filename for context extraction
        max_tags: Maximum number of hashtags to generate
    
    Returns:
        Dict with hashtags list, rationale, and metadata
    """
    if not XAI_API_KEY:
        return _fallback_hashtags(influencer, media_filename, max_tags)
    
    persona = PERSONA_CONFIG.get(influencer, PERSONA_CONFIG["starbright_monroe"])
    context = _extract_context_from_filename(media_filename or "")
    time_context = _get_time_context()
    
    prompt = f"""Generate {max_tags} optimized Twitter/X hashtags for maximum reach and engagement.

PERSONA:
- Name: {persona['name']}
- Style: {persona['style']}
- Target Audience: {persona['audience']}
- Content Type: {persona['content_type']}

CURRENT POST CONTEXT:
- Caption: "{caption}"
- Outfit: {context['outfit']}
- Setting: {context['setting']}
- Time: {time_context['time_of_day']} on {time_context['weekday']}
- Weekend: {'Yes' if time_context['is_weekend'] else 'No'}

STRICT RULES:
1. NEVER use any AI-related hashtags (no #ai, #aimodel, #aigirl, #aibeauty, #aigenerated, etc.)
2. Focus on REACH and ENGAGEMENT, not describing the content
3. Mix: 2 broad discovery tags + 2 engagement/conversational tags + 1 niche high-intent tag
4. Keep hashtags lowercase with # prefix
5. Avoid overly generic tags like #photo or #instagram

HASHTAG STRATEGY:
- Broad tags: High volume, drives impressions (#model, #bikini, #beauty)
- Engagement tags: Conversation starters, time-relevant (#goodmorning, #weekendvibes)
- Niche tags: Specific audience targeting (#bikinigirl, #beachbabe)

Return ONLY a JSON object in this exact format:
{{"hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"], "strategy": "brief explanation"}}"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{XAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {XAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-3-mini",
                    "messages": [
                        {"role": "system", "content": "You are a social media marketing expert specializing in hashtag optimization for maximum reach. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()
                
                import json
                result = json.loads(content)
                hashtags = result.get("hashtags", [])
                
                hashtags = _filter_forbidden(hashtags)
                
                return {
                    "hashtags": hashtags[:max_tags],
                    "strategy": result.get("strategy", "AI-optimized for reach"),
                    "source": "grok",
                    "context": {
                        "outfit": context["outfit"],
                        "setting": context["setting"],
                        "time": time_context["time_of_day"]
                    }
                }
            else:
                print(f"Grok API error: {response.status_code} - {response.text}")
                return _fallback_hashtags(influencer, media_filename, max_tags)
                
    except Exception as e:
        print(f"Hashtag generation error: {e}")
        return _fallback_hashtags(influencer, media_filename, max_tags)


def _fallback_hashtags(
    influencer: str,
    media_filename: Optional[str],
    max_tags: int
) -> Dict[str, Any]:
    """
    Fallback hashtag generation using curated pools (no LLM).
    Uses weighted random selection for variety.
    """
    pools = EVERGREEN_POOLS.get(influencer, EVERGREEN_POOLS["starbright_monroe"])
    context = _extract_context_from_filename(media_filename or "")
    time_context = _get_time_context()
    
    selected = []
    
    reach_tags = random.sample(pools["reach"], min(2, len(pools["reach"])))
    selected.extend(reach_tags)
    
    engagement_tags = pools["engagement"].copy()
    if time_context["time_of_day"] == "morning":
        if "#goodmorning" in engagement_tags:
            selected.append("#goodmorning")
            engagement_tags.remove("#goodmorning")
    if time_context["is_weekend"]:
        if "#weekendvibes" in engagement_tags:
            selected.append("#weekendvibes")
            engagement_tags.remove("#weekendvibes")
    
    while len(selected) < max_tags - 1 and engagement_tags:
        tag = random.choice(engagement_tags)
        if tag not in selected:
            selected.append(tag)
            engagement_tags.remove(tag)
    
    niche_tags = pools["niche"].copy()
    if context["setting"] == "beach" and "#beachbabe" in niche_tags:
        selected.append("#beachbabe")
    elif context["setting"] == "poolside" and "#poolside" in niche_tags:
        selected.append("#poolside")
    elif niche_tags:
        selected.append(random.choice(niche_tags))
    
    selected = _filter_forbidden(selected)
    
    seen = set()
    unique = []
    for tag in selected:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            unique.append(tag)
    
    return {
        "hashtags": unique[:max_tags],
        "strategy": "Curated pool selection with context awareness",
        "source": "fallback",
        "context": {
            "outfit": context["outfit"],
            "setting": context["setting"],
            "time": time_context["time_of_day"]
        }
    }


def format_hashtags(hashtags: List[str], max_chars: Optional[int] = None) -> str:
    """
    Format hashtags into a string, respecting character limits.
    
    Args:
        hashtags: List of hashtag strings
        max_chars: Optional max characters for the hashtag string
    
    Returns:
        Space-separated hashtag string
    """
    if not max_chars:
        return " ".join(hashtags)
    
    result = []
    current_length = 0
    
    for tag in hashtags:
        tag_length = len(tag) + (1 if result else 0)
        if current_length + tag_length <= max_chars:
            result.append(tag)
            current_length += tag_length
        else:
            break
    
    return " ".join(result)
