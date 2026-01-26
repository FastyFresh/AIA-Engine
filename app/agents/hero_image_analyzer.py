"""
Hero Image Analyzer Agent
Analyzes uploaded hero images using vision LLM to auto-generate descriptive filenames.
"""
import os
import base64
import httpx
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

XAI_API_KEY = os.getenv("XAI_API_KEY")

OUTFIT_KEYWORDS = [
    "bikini", "swimsuit", "shorts", "dress", "lingerie", "jeans", 
    "yoga", "athletic", "casual", "formal", "sundress", "tank_top",
    "crop_top", "skirt", "leggings", "bodysuit", "romper"
]

SETTING_KEYWORDS = [
    "beach", "pool", "poolside", "bedroom", "studio", "outdoor",
    "nature", "gym", "bathroom", "kitchen", "living_room", "balcony",
    "garden", "rooftop", "sunset", "morning", "night"
]

MOOD_KEYWORDS = [
    "playful", "sultry", "casual", "elegant", "sporty", "cozy",
    "glamorous", "natural", "confident", "relaxed"
]


async def analyze_hero_image(
    image_path: str,
    influencer: str = "starbright_monroe"
) -> Dict[str, Any]:
    """
    Analyze a hero image using XAI/Grok vision to extract context.
    
    Args:
        image_path: Path to the image file
        influencer: Target influencer persona
        
    Returns:
        Dict with detected outfit, setting, mood, and suggested filename
    """
    if not XAI_API_KEY:
        return {
            "success": False,
            "error": "XAI_API_KEY not configured",
            "fallback_name": _generate_fallback_name(influencer)
        }
    
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        ext = Path(image_path).suffix.lower()
        if ext in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif ext == ".png":
            mime_type = "image/png"
        elif ext == ".webp":
            mime_type = "image/webp"
        else:
            mime_type = "image/jpeg"
        
        persona_name = "Starbright Monroe" if "starbright" in influencer else "Luna Vale"
        
        prompt = f"""Analyze this image of {persona_name} for content tagging purposes.

Describe in a structured way:
1. OUTFIT: What is she wearing? Pick the most specific term (bikini, shorts, dress, swimsuit, tank_top, crop_top, lingerie, athletic, casual, etc.)
2. SETTING: Where is she? (beach, pool, bedroom, studio, outdoor, bathroom, gym, balcony, garden, etc.)
3. MOOD: What's the vibe? (playful, sultry, casual, elegant, sporty, cozy, natural, confident, relaxed)
4. DETAILS: Any notable details? (colors, time of day like sunset/morning, specific poses)

Respond in this exact JSON format:
{{
    "outfit": "single_word",
    "setting": "single_word", 
    "mood": "single_word",
    "details": "one_or_two_words",
    "description": "Brief one-sentence description"
}}

Use lowercase, underscores for multi-word terms. Be specific and accurate."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {XAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-2-vision-1212",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{image_data}"
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "max_tokens": 300
                }
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "fallback_name": _generate_fallback_name(influencer)
                }
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            parsed = _parse_analysis_response(content)
            suggested_name = _generate_filename(influencer, parsed)
            
            return {
                "success": True,
                "outfit": parsed.get("outfit", "casual"),
                "setting": parsed.get("setting", "studio"),
                "mood": parsed.get("mood", "natural"),
                "details": parsed.get("details", ""),
                "description": parsed.get("description", ""),
                "suggested_filename": suggested_name,
                "raw_response": content
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fallback_name": _generate_fallback_name(influencer)
        }


def _parse_analysis_response(content: str) -> Dict[str, str]:
    """Parse the LLM response to extract structured data"""
    import json
    import re
    
    json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    result = {
        "outfit": "casual",
        "setting": "studio",
        "mood": "natural",
        "details": ""
    }
    
    content_lower = content.lower()
    
    for keyword in OUTFIT_KEYWORDS:
        if keyword in content_lower:
            result["outfit"] = keyword
            break
    
    for keyword in SETTING_KEYWORDS:
        if keyword in content_lower:
            result["setting"] = keyword
            break
            
    for keyword in MOOD_KEYWORDS:
        if keyword in content_lower:
            result["mood"] = keyword
            break
    
    return result


def _generate_filename(influencer: str, analysis: Dict[str, str]) -> str:
    """Generate a descriptive filename from analysis"""
    persona = "starbright" if "starbright" in influencer else "luna"
    outfit = analysis.get("outfit", "casual").replace(" ", "_").lower()
    setting = analysis.get("setting", "studio").replace(" ", "_").lower()
    details = analysis.get("details", "").replace(" ", "_").lower()
    
    if details and len(details) < 20:
        filename = f"{persona}_{setting}_{outfit}_{details}"
    else:
        filename = f"{persona}_{setting}_{outfit}"
    
    filename = "".join(c for c in filename if c.isalnum() or c == "_")
    filename = "_".join(filter(None, filename.split("_")))
    
    return filename


def _generate_fallback_name(influencer: str) -> str:
    """Generate a fallback filename with timestamp"""
    import time
    persona = "starbright" if "starbright" in influencer else "luna"
    timestamp = int(time.time())
    return f"{persona}_hero_{timestamp}"


async def process_uploaded_hero(
    temp_path: str,
    influencer: str,
    custom_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process an uploaded hero image: analyze, rename, and save to correct folder.
    
    Args:
        temp_path: Path to the temporarily uploaded file
        influencer: Target influencer persona
        custom_name: Optional custom filename override
        
    Returns:
        Dict with success status and final file path
    """
    hero_dir = Path(f"content/references/{influencer}/hero")
    hero_dir.mkdir(parents=True, exist_ok=True)
    
    if custom_name:
        base_name = custom_name.replace(" ", "_").lower()
        base_name = "".join(c for c in base_name if c.isalnum() or c == "_")
    else:
        analysis = await analyze_hero_image(temp_path, influencer)
        if analysis.get("success"):
            base_name = analysis["suggested_filename"]
        else:
            base_name = analysis.get("fallback_name", _generate_fallback_name(influencer))
    
    ext = Path(temp_path).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"
    
    final_name = f"{base_name}{ext}"
    final_path = hero_dir / final_name
    
    counter = 1
    while final_path.exists():
        final_name = f"{base_name}_{counter}{ext}"
        final_path = hero_dir / final_name
        counter += 1
    
    import shutil
    shutil.move(temp_path, str(final_path))
    
    analysis_result = await analyze_hero_image(str(final_path), influencer) if not custom_name else {}
    
    return {
        "success": True,
        "filename": final_name,
        "path": str(final_path),
        "influencer": influencer,
        "analysis": analysis_result if not custom_name else None
    }
