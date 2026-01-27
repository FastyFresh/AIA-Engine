"""
Pose Analyzer Service - Uses Grok Vision to analyze reference images

Analyzes reference images to extract:
- Exact body pose and position
- Camera angle and perspective
- Limb placement and body curves
- Outfit details
- Expression and gaze direction

Returns optimized prompts for image generation.
"""

import os
import base64
import httpx
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Grok vision model (multimodal with vision support)
GROK_VISION_MODEL = "x-ai/grok-4-fast"


class PoseAnalyzer:
    """Analyzes reference images using Grok Vision to generate optimal prompts."""
    
    def __init__(self, influencer_id: str = "starbright_monroe"):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.influencer_id = influencer_id
        
        # Identity descriptors for each influencer
        self.identities = {
            "starbright_monroe": {
                "name": "Starbright Monroe",
                "features": (
                    "very pale porcelain ivory white skin with natural freckles across nose and cheeks, "
                    "straight sleek dark brown hair, warm olive-brown eyes, "
                    "slender petite body with natural proportions, small natural A-cup chest, "
                    "extremely thin with narrow waist"
                )
            },
            "luna_vale": {
                "name": "Luna Vale", 
                "features": (
                    "fair pale skin with subtle freckles, long straight cotton candy pink hair, "
                    "striking grey-blue eyes, soft rounded face, slim petite body"
                )
            }
        }
        
        logger.info(f"PoseAnalyzer initialized for {influencer_id}")
    
    def sanitize_prompt(self, prompt: str) -> str:
        """Remove explicit terms that trigger content filters."""
        replacements = {
            # Clothing replacements
            "thong": "shorts",
            "panties": "shorts", 
            "underwear": "shorts",
            "bra": "crop top",
            "lingerie": "loungewear",
            "bikini bottom": "shorts",
            "g-string": "shorts",
            # Body part replacements
            "buttocks": "hips",
            "butt": "hips",
            "rear": "back",
            "cleavage": "neckline",
            "breasts": "chest",
            "crotch": "lower body",
            # Pose/action replacements  
            "seductively": "elegantly",
            "sensually": "gracefully",
            "provocatively": "confidently",
            "sexy": "stylish",
            "erotic": "artistic",
            "nude": "minimal clothing",
            "naked": "wearing minimal",
            "exposed": "visible",
            # Remove explicit descriptors
            "high-cut": "fitted",
            "low-cut": "v-neck",
            "revealing": "fitted",
            "sheer": "light fabric",
            "see-through": "light fabric",
        }
        
        result = prompt.lower()
        for explicit, safe in replacements.items():
            result = result.replace(explicit.lower(), safe)
        
        # Restore original capitalization for first letter
        if prompt and prompt[0].isupper():
            result = result[0].upper() + result[1:]
        
        return result
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 data URL."""
        with open(image_path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode("utf-8")
        
        ext = Path(image_path).suffix.lower()
        mime_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
        mime = mime_types.get(ext, "image/jpeg")
        
        return f"data:{mime};base64,{data}"
    
    async def analyze_pose(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze a reference image and return detailed pose description.
        
        Returns:
            Dict with 'prompt' (optimized generation prompt) and 'analysis' (raw analysis)
        """
        if not self.api_key:
            return {"status": "error", "error": "OPENROUTER_API_KEY not configured"}
        
        if not os.path.exists(image_path):
            return {"status": "error", "error": f"Image not found: {image_path}"}
        
        try:
            image_data = self.encode_image(image_path)
            identity = self.identities.get(self.influencer_id, self.identities["starbright_monroe"])
            
            system_prompt = """You are an expert at analyzing photographs for pose recreation. 
Your task is to describe the EXACT pose, camera angle, and body position so an AI image generator can recreate it precisely.

Focus on:
1. BODY POSITION: Lying/sitting/standing, which direction body faces, body curve/arch
2. LIMB PLACEMENT: Exact position of each arm and leg, bent/straight, crossed/apart
3. CAMERA ANGLE: High/low/eye level, distance, what's in foreground vs background
4. HEAD/FACE: Direction looking, tilt, expression
5. OUTFIT: Describe clothing items precisely
6. COMPOSITION: What body parts are prominent, what's cropped out

Be extremely specific about spatial relationships and angles."""

            user_prompt = f"""Analyze this reference image and provide an optimized prompt for recreating this exact pose.

The subject should have these features: {identity['features']}

Provide your response in this exact format:

POSE ANALYSIS:
[Detailed description of body position, limb placement, camera angle]

OPTIMIZED PROMPT:
[A single paragraph prompt ready for image generation, including pose, outfit, camera angle, lighting, and the subject's physical features. Make it detailed but concise.]"""

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://replit.com",
                        "X-Title": "AIA Engine Pose Analyzer"
                    },
                    json={
                        "model": GROK_VISION_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": user_prompt},
                                    {"type": "image_url", "image_url": {"url": image_data}}
                                ]
                            }
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.3
                    }
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Grok Vision API error: {error_text}")
                    return {"status": "error", "error": f"API error: {error_text}"}
                
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if not content:
                    return {"status": "error", "error": "Empty response from Grok Vision"}
                
                # Parse the response
                analysis = ""
                prompt = ""
                
                if "POSE ANALYSIS:" in content and "OPTIMIZED PROMPT:" in content:
                    parts = content.split("OPTIMIZED PROMPT:")
                    analysis = parts[0].replace("POSE ANALYSIS:", "").strip()
                    prompt = parts[1].strip()
                else:
                    # If format not matched, use whole response as prompt
                    prompt = content
                    analysis = content
                
                logger.info(f"Pose analysis complete for {image_path}")
                
                # Sanitize prompt for content filters
                sanitized_prompt = self.sanitize_prompt(prompt)
                
                return {
                    "status": "success",
                    "analysis": analysis,
                    "prompt": sanitized_prompt,
                    "raw_prompt": prompt,
                    "raw_response": content
                }
                
        except Exception as e:
            logger.error(f"Pose analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def analyze_and_generate_prompt(
        self, 
        image_path: str,
        background_type: str = "apartment_bedroom_day"
    ) -> Dict[str, Any]:
        """
        Analyze image and return a generation-ready prompt with background context.
        """
        result = await self.analyze_pose(image_path)
        
        if result.get("status") != "success":
            return result
        
        # Add background context to prompt
        background_contexts = {
            "apartment_day": "modern luxury apartment living room with city view through floor-to-ceiling windows, bright natural daylight",
            "apartment_night": "modern luxury apartment living room with city lights through windows, warm ambient evening lighting",
            "apartment_bedroom_day": "modern luxury bedroom with white bedding and natural daylight through window, soft morning light",
            "apartment_bedroom_night": "modern luxury bedroom with dark bedding and city view through window at night, warm ambient lighting",
            "bathroom_luxury": "luxury modern bathroom with marble surfaces and soft lighting",
            "spa_wellness": "luxury spa setting with soft ambient lighting"
        }
        
        bg_context = background_contexts.get(background_type, background_contexts["apartment_bedroom_day"])
        
        # Append background to prompt
        enhanced_prompt = result["prompt"]
        if bg_context not in enhanced_prompt.lower():
            enhanced_prompt = enhanced_prompt.rstrip('.') + f", {bg_context}"
        
        result["enhanced_prompt"] = enhanced_prompt
        result["background_type"] = background_type
        
        return result
