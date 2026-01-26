"""
Prompt Intelligence Service - Image-to-Prompt Analysis

Uses sophisticated vision models to analyze competitor images and generate
optimized prompts for Seedream 4.5 generation.

Models:
- CogVLM: Dense compositional descriptions (pose, scene, outfit, lighting)
- CLIP Interrogator: Aesthetic tags, style descriptors, SD-optimized prompts
- Grok Vision: High-level scene understanding, persona alignment refinement
"""

import os
import httpx
import asyncio
import logging
import json
import base64
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
COGVLM_MODEL = "cjwbw/cogvlm:a4a8bafd6089e1716b06057c42b19378250d008b80fe87caa5cd36d40c1eda90"
CLIP_INTERROGATOR_MODEL = "pharmapsychotic/clip-interrogator:a4a8bafd6089e1716b06057c42b19378250d008b80fe87caa5cd36d40c1eda90"

ANALYSIS_TIMEOUT = 300
MAX_RETRIES = 2


class PromptIntelligenceService:
    """
    Analyzes images and generates optimized prompts for AI influencer generation.
    
    Workflow:
    1. CogVLM extracts detailed scene description
    2. CLIP Interrogator extracts aesthetic/style tags
    3. Grok Vision refines and aligns with persona
    4. Structured output feeds into PromptBuilder
    """
    
    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
        self.xai_api_key = os.getenv("XAI_API_KEY", "")
        self.cache_dir = Path("content/prompt_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("PromptIntelligenceService initialized")
        logger.info(f"Replicate API: {'configured' if self.replicate_token else 'missing'}")
        logger.info(f"XAI/Grok API: {'configured' if self.xai_api_key else 'missing'}")
    
    def _get_image_url(self, image_path: str) -> Optional[str]:
        """Convert local path to data URL or return URL if already a URL."""
        if image_path.startswith("http://") or image_path.startswith("https://"):
            return image_path
        
        path = Path(image_path)
        if not path.exists():
            logger.error(f"Image not found: {image_path}")
            return None
        
        with open(path, "rb") as f:
            image_data = f.read()
        
        ext = path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif"
        }
        mime_type = mime_types.get(ext, "image/jpeg")
        
        b64_data = base64.b64encode(image_data).decode("utf-8")
        return f"data:{mime_type};base64,{b64_data}"
    
    async def _extract_instagram_image_url(self, html_content: str) -> Optional[str]:
        """Extract actual image URL from Instagram HTML page using og:image meta tag."""
        import re
        import html as html_lib
        
        patterns = [
            r'og:image["\']?\s*content=["\']([^"\']+)["\']',
            r'content=["\']([^"\']+)["\'].*?property=["\']og:image',
            r'property=["\']og:image["\'].*?content=["\']([^"\']+)',
            r'"display_url"\s*:\s*"([^"]+)"',
            r'cdninstagram\.com[^"\']*\.jpg[^"\']*',
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, html_content)
            if match:
                if i == 4:
                    image_url = match.group(0)
                    if not image_url.startswith('http'):
                        image_url = 'https://' + image_url
                else:
                    image_url = match.group(1)
                image_url = html_lib.unescape(image_url)
                image_url = image_url.replace("\\u0026", "&")
                logger.info(f"Extracted Instagram image URL (pattern {i}): {image_url[:100]}...")
                return image_url
        
        if 'cdninstagram.com' in html_content:
            logger.warning(f"Found cdninstagram.com in HTML but patterns didn't match. Sample: {html_content[html_content.find('cdninstagram.com')-50:html_content.find('cdninstagram.com')+100]}")
        
        return None
    
    async def download_image(self, url: str) -> Optional[str]:
        """Download image from URL and save to temp directory with unique name."""
        if not url.startswith("http://") and not url.startswith("https://"):
            return url
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    logger.error(f"Failed to download image: {response.status_code}")
                    return None
                
                content_type = response.headers.get("content-type", "")
                
                if "text/html" in content_type or "instagram.com" in url:
                    html_content = response.text
                    actual_image_url = await self._extract_instagram_image_url(html_content)
                    
                    if actual_image_url:
                        logger.info(f"Downloading actual image from extracted URL")
                        img_response = await client.get(actual_image_url, headers=headers)
                        if img_response.status_code == 200:
                            response = img_response
                            content_type = img_response.headers.get("content-type", "image/jpeg")
                        else:
                            logger.error(f"Failed to download extracted image: {img_response.status_code}")
                            return None
                    else:
                        logger.error("Could not extract image URL from Instagram page")
                        return None
                
                ext = ".jpg"
                if "png" in content_type:
                    ext = ".png"
                elif "webp" in content_type:
                    ext = ".webp"
                
                temp_dir = Path("content/temp_downloads")
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                unique_id = uuid.uuid4().hex[:8]
                filename = f"competitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{unique_id}{ext}"
                filepath = temp_dir / filename
                
                filepath.write_bytes(response.content)
                logger.info(f"Downloaded competitor image: {filepath}")
                
                return str(filepath)
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None
    
    def is_url(self, path: str) -> bool:
        """Check if path is a URL."""
        return path.startswith("http://") or path.startswith("https://")
    
    async def resolve_image_path(self, image_input: str) -> Optional[str]:
        """Resolve image input to local path, downloading if URL."""
        if self.is_url(image_input):
            return await self.download_image(image_input)
        if Path(image_input).exists():
            return image_input
        return None
    
    async def _call_replicate_with_retry(
        self,
        model_version: str,
        input_data: Dict[str, Any],
        timeout: int = ANALYSIS_TIMEOUT,
        max_retries: int = MAX_RETRIES
    ) -> Dict[str, Any]:
        """Call Replicate API with retry logic for cold starts/timeouts."""
        last_error = None
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                wait_time = 5 * attempt
                logger.info(f"Retry {attempt}/{max_retries} after {wait_time}s wait...")
                await asyncio.sleep(wait_time)
            
            result = await self._call_replicate(model_version, input_data, timeout)
            
            if result.get("status") == "success":
                return result
            
            last_error = result.get("error", "Unknown error")
            if "Timeout" in str(last_error) or "starting" in str(last_error).lower():
                logger.warning(f"Attempt {attempt + 1} failed (likely cold start): {last_error}")
                continue
            else:
                return result
        
        return {"status": "error", "error": f"Failed after {max_retries + 1} attempts: {last_error}"}
    
    async def _call_replicate(
        self,
        model_version: str,
        input_data: Dict[str, Any],
        timeout: int = ANALYSIS_TIMEOUT
    ) -> Dict[str, Any]:
        """Call Replicate API and wait for result."""
        if not self.replicate_token:
            return {"status": "error", "error": "REPLICATE_API_TOKEN not configured"}
        
        headers = {
            "Authorization": f"Token {self.replicate_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "version": model_version.split(":")[-1],
            "input": input_data
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    REPLICATE_API_URL,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 201:
                    return {"status": "error", "error": f"API error: {response.status_code} - {response.text}"}
                
                result = response.json()
                prediction_id = result.get("id")
                status_url = f"{REPLICATE_API_URL}/{prediction_id}"
                
                start_time = asyncio.get_event_loop().time()
                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        return {"status": "error", "error": f"Timeout after {timeout}s"}
                    
                    await asyncio.sleep(2)
                    
                    status_response = await client.get(status_url, headers=headers)
                    status_data = status_response.json()
                    status = status_data.get("status")
                    
                    if status == "succeeded":
                        return {
                            "status": "success",
                            "output": status_data.get("output"),
                            "metrics": status_data.get("metrics", {})
                        }
                    elif status == "failed":
                        return {"status": "error", "error": status_data.get("error", "Unknown error")}
                    elif status == "canceled":
                        return {"status": "error", "error": "Prediction canceled"}
        except httpx.TimeoutException:
            return {"status": "error", "error": f"Timeout after {timeout}s"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def analyze_with_cogvlm(
        self,
        image_path: str,
        prompt: str = "Describe this image in comprehensive detail. Include: the person's pose, body position, facial expression, outfit/clothing with colors and materials, hairstyle, makeup, setting/background, lighting conditions, camera angle, and overall mood/aesthetic."
    ) -> Dict[str, Any]:
        """
        Analyze image with CogVLM for detailed scene description.
        
        Returns structured description of pose, outfit, setting, lighting, etc.
        """
        logger.info(f"Analyzing with CogVLM: {image_path}")
        
        image_url = self._get_image_url(image_path)
        if not image_url:
            return {"status": "error", "error": "Failed to process image"}
        
        input_data = {
            "image": image_url,
            "prompt": prompt,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        result = await self._call_replicate_with_retry(COGVLM_MODEL, input_data)
        
        if result.get("status") == "success":
            output = result.get("output", "")
            if isinstance(output, list):
                output = "".join(output)
            
            return {
                "status": "success",
                "description": output,
                "model": "cogvlm",
                "image": image_path
            }
        
        return result
    
    async def analyze_with_clip_interrogator(
        self,
        image_path: str,
        mode: str = "best"
    ) -> Dict[str, Any]:
        """
        Analyze image with CLIP Interrogator for aesthetic/style tags.
        
        Modes: 'best', 'fast', 'classic', 'negative'
        Returns SD-optimized prompt with style descriptors.
        """
        logger.info(f"Analyzing with CLIP Interrogator: {image_path}")
        
        image_url = self._get_image_url(image_path)
        if not image_url:
            return {"status": "error", "error": "Failed to process image"}
        
        input_data = {
            "image": image_url,
            "clip_model_name": "ViT-L-14/openai",
            "mode": mode
        }
        
        result = await self._call_replicate_with_retry(CLIP_INTERROGATOR_MODEL, input_data)
        
        if result.get("status") == "success":
            output = result.get("output", "")
            
            return {
                "status": "success",
                "style_prompt": output,
                "model": "clip-interrogator",
                "mode": mode,
                "image": image_path
            }
        
        return result
    
    async def analyze_with_grok_vision(
        self,
        image_path: str,
        analysis_focus: str = "influencer_content"
    ) -> Dict[str, Any]:
        """
        Analyze image with Grok Vision for high-level understanding.
        
        Focus areas:
        - influencer_content: Pose, outfit, setting for influencer replication
        - brand_alignment: Check if content aligns with persona
        - quality_assessment: Technical quality evaluation
        """
        if not self.xai_api_key:
            return {"status": "error", "error": "XAI_API_KEY not configured"}
        
        logger.info(f"Analyzing with Grok Vision: {image_path}")
        
        image_url = self._get_image_url(image_path)
        if not image_url:
            return {"status": "error", "error": "Failed to process image"}
        
        prompts = {
            "influencer_content": """Analyze this influencer photo for content recreation. Provide a structured breakdown:

1. POSE: Exact body position, hand placement, head tilt, gaze direction
2. EXPRESSION: Facial expression, mood, emotion conveyed
3. OUTFIT: Detailed clothing description with colors, materials, style
4. SETTING: Background, environment, props visible
5. LIGHTING: Light source direction, quality (soft/hard), color temperature
6. CAMERA: Angle, distance, framing (close-up/full-body/mid-shot)
7. AESTHETIC: Overall vibe, style category (glamour/casual/artistic/etc)
8. ENGAGEMENT ELEMENTS: What makes this image compelling for social media

Format as structured JSON.""",
            
            "brand_alignment": """Evaluate if this image would be appropriate for a glamorous AI influencer persona. Consider:
- Professionalism and quality
- Aesthetic appeal
- Social media suitability
- Any concerning elements

Provide a score 1-10 and brief explanation.""",
            
            "quality_assessment": """Assess the technical quality of this image:
- Resolution and sharpness
- Lighting quality
- Composition
- Color balance
- Overall production value

Provide scores and specific observations."""
        }
        
        prompt = prompts.get(analysis_focus, prompts["influencer_content"])
        
        headers = {
            "Authorization": f"Bearer {self.xai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "grok-2-vision-latest",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    return {"status": "error", "error": f"Grok API error: {response.status_code}"}
                
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return {
                    "status": "success",
                    "analysis": content,
                    "model": "grok-2-vision",
                    "focus": analysis_focus,
                    "image": image_path
                }
                
            except Exception as e:
                logger.error(f"Grok Vision error: {e}")
                return {"status": "error", "error": str(e)}
    
    async def full_analysis(
        self,
        image_input: str,
        include_clip: bool = True,
        include_grok: bool = True
    ) -> Dict[str, Any]:
        """
        Run comprehensive analysis using all available models.
        
        Accepts both local file paths and URLs.
        Combines outputs into a unified prompt recommendation.
        """
        image_path = await self.resolve_image_path(image_input)
        if not image_path:
            return {"status": "error", "error": f"Could not resolve image: {image_input}"}
        
        logger.info(f"Running full analysis: {image_path} (original: {image_input})")
        
        tasks = [self.analyze_with_cogvlm(image_path)]
        
        if include_clip:
            tasks.append(self.analyze_with_clip_interrogator(image_path))
        
        if include_grok and self.xai_api_key:
            tasks.append(self.analyze_with_grok_vision(image_path))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        analysis = {
            "status": "success",
            "image": image_path,
            "original_input": image_input,
            "timestamp": datetime.now().isoformat(),
            "cogvlm": None,
            "clip_interrogator": None,
            "grok_vision": None,
            "combined_prompt": None
        }
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Analysis task {i} failed: {result}")
                continue
            
            if isinstance(result, dict) and result.get("status") == "success":
                model = result.get("model", "")
                if model == "cogvlm":
                    analysis["cogvlm"] = result.get("description")
                elif model == "clip-interrogator":
                    analysis["clip_interrogator"] = result.get("style_prompt")
                elif model == "grok-2-vision":
                    analysis["grok_vision"] = result.get("analysis")
        
        analysis["combined_prompt"] = self._combine_analysis(analysis)
        
        cache_file = self.cache_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(cache_file, "w") as f:
            json.dump(analysis, f, indent=2)
        
        return analysis
    
    def _combine_analysis(self, analysis: Dict[str, Any]) -> str:
        """
        Combine multiple analysis outputs into an optimized prompt.
        
        Priority:
        1. CLIP Interrogator for style tags (if available)
        2. CogVLM for scene description (if available)
        3. Grok Vision for structured breakdown (fallback when others unavailable)
        """
        parts = []
        has_replicate_data = False
        
        if analysis.get("clip_interrogator"):
            clip_prompt = analysis["clip_interrogator"]
            style_parts = [p.strip() for p in clip_prompt.split(",")[:10]]
            parts.extend(style_parts)
            has_replicate_data = True
        
        if analysis.get("cogvlm"):
            cogvlm_desc = analysis["cogvlm"]
            if len(cogvlm_desc) > 500:
                cogvlm_desc = cogvlm_desc[:500] + "..."
            parts.append(cogvlm_desc)
            has_replicate_data = True
        
        if not has_replicate_data and analysis.get("grok_vision"):
            grok_analysis = analysis["grok_vision"]
            grok_prompt = self._extract_prompt_from_grok(grok_analysis)
            if grok_prompt:
                parts.append(grok_prompt)
                logger.info("Using Grok Vision fallback for prompt generation")
        
        combined = ", ".join(parts) if parts else ""
        
        combined = combined.replace("woman", "Starbright Monroe")
        combined = combined.replace("girl", "Starbright Monroe")
        combined = combined.replace("lady", "Starbright Monroe")
        combined = combined.replace("model", "Starbright Monroe")
        combined = combined.replace("person", "Starbright Monroe")
        
        quality_suffix = ", professional photography, 8K resolution, Canon EOS R5, 85mm f/1.4 lens, natural lighting, photorealistic, hyper-detailed skin texture"
        
        return combined + quality_suffix
    
    def _extract_prompt_from_grok(self, grok_analysis: str) -> str:
        """
        Extract structured prompt from Grok Vision analysis.
        
        Handles both JSON and plain-text responses from Grok.
        """
        if not grok_analysis or not grok_analysis.strip():
            return ""
        
        try:
            json_match = grok_analysis
            if "```json" in grok_analysis:
                json_match = grok_analysis.split("```json")[1].split("```")[0]
            elif "```" in grok_analysis and "{" in grok_analysis:
                json_match = grok_analysis.split("```")[1].split("```")[0]
            elif grok_analysis.strip().startswith("{"):
                json_match = grok_analysis
            else:
                return self._extract_prompt_from_plain_text(grok_analysis)
            
            data = json.loads(json_match.strip())
            
            prompt_parts = []
            
            if "POSE" in data:
                pose = data["POSE"]
                if isinstance(pose, dict):
                    pose_desc = ", ".join([f"{k}: {v}" for k, v in pose.items() if v])
                else:
                    pose_desc = str(pose)
                prompt_parts.append(f"pose: {pose_desc}")
            
            if "EXPRESSION" in data:
                expr = data["EXPRESSION"]
                if isinstance(expr, dict):
                    expr_desc = ", ".join([str(v) for v in expr.values() if v])
                else:
                    expr_desc = str(expr)
                prompt_parts.append(f"expression: {expr_desc}")
            
            if "OUTFIT" in data:
                outfit = data["OUTFIT"]
                if isinstance(outfit, dict):
                    outfit_desc = ", ".join([str(v) for v in outfit.values() if v])
                else:
                    outfit_desc = str(outfit)
                prompt_parts.append(f"wearing {outfit_desc}")
            
            if "SETTING" in data:
                setting = data["SETTING"]
                if isinstance(setting, dict):
                    setting_desc = ", ".join([str(v) for v in setting.values() if v])
                else:
                    setting_desc = str(setting)
                prompt_parts.append(f"in {setting_desc}")
            
            if "LIGHTING" in data:
                lighting = data["LIGHTING"]
                if isinstance(lighting, dict):
                    lighting_desc = ", ".join([str(v) for v in lighting.values() if v])
                else:
                    lighting_desc = str(lighting)
                prompt_parts.append(f"lighting: {lighting_desc}")
            
            if "AESTHETIC" in data:
                aesthetic = data["AESTHETIC"]
                if isinstance(aesthetic, dict):
                    aesthetic_desc = ", ".join([str(v) for v in aesthetic.values() if v])
                else:
                    aesthetic_desc = str(aesthetic)
                prompt_parts.append(f"style: {aesthetic_desc}")
            
            if prompt_parts:
                return ", ".join(prompt_parts)
            else:
                return self._extract_prompt_from_plain_text(grok_analysis)
            
        except (json.JSONDecodeError, KeyError, TypeError, IndexError, ValueError) as e:
            logger.info(f"JSON parsing failed, extracting from plain text: {e}")
            extracted = self._extract_prompt_from_plain_text(grok_analysis)
            if extracted:
                return extracted
            if len(grok_analysis) > 800:
                return grok_analysis[:800].rsplit(" ", 1)[0] + "..."
            return grok_analysis
    
    def _extract_prompt_from_plain_text(self, text: str) -> str:
        """Extract prompt elements from plain-text Grok response."""
        prompt_parts = []
        text_lower = text.lower()
        
        key_patterns = {
            "pose": ["pose:", "body position:", "standing", "sitting", "lying", "leaning"],
            "expression": ["expression:", "facial expression:", "smiling", "serious", "confident"],
            "outfit": ["wearing", "outfit:", "dressed in", "clothing:", "attire:"],
            "setting": ["setting:", "background:", "environment:", "location:"],
            "lighting": ["lighting:", "light:", "illuminated", "soft light", "natural light"]
        }
        
        lines = text.split("\n")
        for line in lines:
            line_clean = line.strip()
            if not line_clean or len(line_clean) < 5:
                continue
            
            for category, patterns in key_patterns.items():
                for pattern in patterns:
                    if pattern in line_clean.lower():
                        cleaned = line_clean.lstrip("0123456789.-) ").strip()
                        if cleaned and len(cleaned) > 10:
                            prompt_parts.append(cleaned)
                            break
        
        if prompt_parts:
            combined = ", ".join(prompt_parts[:8])
            if len(combined) > 800:
                combined = combined[:800].rsplit(",", 1)[0]
            return combined
        
        if len(text) > 800:
            return text[:800].rsplit(" ", 1)[0] + "..."
        return text
    
    def _build_detailed_seedream_prompt(self, grok_analysis: str, persona: str = "starbright_monroe") -> str:
        """
        Build a highly detailed Seedream 4.5 prompt from Grok Vision analysis.
        Produces photorealistic prompts with camera specs, lighting, and scene details.
        """
        if not grok_analysis:
            return ""
        
        try:
            json_match = grok_analysis
            if "```json" in grok_analysis:
                json_match = grok_analysis.split("```json")[1].split("```")[0]
            elif "```" in grok_analysis and "{" in grok_analysis:
                json_match = grok_analysis.split("```")[1].split("```")[0]
            
            data = json.loads(json_match.strip())
            
            persona_name = "Starbright Monroe" if "starbright" in persona.lower() else "Luna Vale"
            
            prompt_parts = []
            
            prompt_parts.append(f"Photorealistic portrait of {persona_name}")
            
            if "POSE" in data and isinstance(data["POSE"], dict):
                pose = data["POSE"]
                pose_details = []
                if pose.get("body_position"):
                    pose_details.append(pose["body_position"])
                if pose.get("hand_placement"):
                    pose_details.append(pose["hand_placement"])
                if pose.get("head_tilt"):
                    pose_details.append(pose["head_tilt"])
                if pose.get("gaze_direction"):
                    pose_details.append(pose["gaze_direction"])
                if pose_details:
                    prompt_parts.append(", ".join(pose_details))
            
            if "EXPRESSION" in data and isinstance(data["EXPRESSION"], dict):
                expr = data["EXPRESSION"]
                expr_details = []
                if expr.get("facial_expression"):
                    expr_details.append(expr["facial_expression"])
                if expr.get("mood"):
                    expr_details.append(f"{expr['mood']} mood")
                if expr.get("emotion_conveyed"):
                    expr_details.append(f"conveying {expr['emotion_conveyed']}")
                if expr_details:
                    prompt_parts.append(", ".join(expr_details))
            
            if "OUTFIT" in data and isinstance(data["OUTFIT"], dict):
                outfit = data["OUTFIT"]
                outfit_parts = []
                if outfit.get("top"):
                    outfit_parts.append(outfit["top"])
                if outfit.get("bottom"):
                    outfit_parts.append(outfit["bottom"])
                if outfit.get("clothing_description"):
                    outfit_parts.append(outfit["clothing_description"])
                if outfit.get("footwear"):
                    outfit_parts.append(outfit["footwear"])
                if outfit.get("colors"):
                    outfit_parts.append(f"colors: {outfit['colors']}")
                if outfit.get("materials"):
                    outfit_parts.append(f"made of {outfit['materials']}")
                if outfit.get("style"):
                    outfit_parts.append(f"{outfit['style']} style")
                if outfit_parts:
                    prompt_parts.append("wearing " + ", ".join(outfit_parts))
            
            if "SETTING" in data and isinstance(data["SETTING"], dict):
                setting = data["SETTING"]
                setting_parts = []
                if setting.get("background"):
                    setting_parts.append(setting["background"])
                if setting.get("environment"):
                    setting_parts.append(setting["environment"])
                if setting.get("props_visible"):
                    setting_parts.append(f"props: {setting['props_visible']}")
                if setting_parts:
                    prompt_parts.append("setting: " + ", ".join(setting_parts))
            
            if "LIGHTING" in data and isinstance(data["LIGHTING"], dict):
                lighting = data["LIGHTING"]
                lighting_parts = []
                if lighting.get("light_source_direction"):
                    lighting_parts.append(lighting["light_source_direction"])
                if lighting.get("quality"):
                    lighting_parts.append(lighting["quality"])
                if lighting.get("color_temperature"):
                    lighting_parts.append(f"{lighting['color_temperature']} color temperature")
                if lighting_parts:
                    prompt_parts.append("lighting: " + ", ".join(lighting_parts))
            
            if "CAMERA" in data and isinstance(data["CAMERA"], dict):
                camera = data["CAMERA"]
                camera_parts = []
                if camera.get("angle"):
                    camera_parts.append(f"{camera['angle']} angle")
                if camera.get("distance"):
                    camera_parts.append(camera["distance"])
                if camera.get("framing"):
                    camera_parts.append(f"{camera['framing']} framing")
                if camera_parts:
                    prompt_parts.append("camera: " + ", ".join(camera_parts))
            
            if "AESTHETIC" in data and isinstance(data["AESTHETIC"], dict):
                aesthetic = data["AESTHETIC"]
                if aesthetic.get("overall_vibe"):
                    prompt_parts.append(f"aesthetic: {aesthetic['overall_vibe']}")
                if aesthetic.get("style_category"):
                    prompt_parts.append(f"style: {aesthetic['style_category']}")
            
            quality_suffix = (
                "Shot on Canon EOS R5, 85mm f/1.4 lens, "
                "8K resolution, RAW format, natural skin texture with visible pores, "
                "photorealistic lighting, hyper-detailed, professional photography, "
                "magazine quality, subtle film grain, sharp focus on eyes"
            )
            prompt_parts.append(quality_suffix)
            
            full_prompt = ". ".join(prompt_parts)
            
            return full_prompt
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse Grok JSON for detailed prompt: {e}")
            return self._extract_prompt_from_grok(grok_analysis)
    
    async def generate_seedream_prompt_fast(
        self,
        image_input: str,
        persona: str = "starbright_monroe"
    ) -> Dict[str, Any]:
        """
        Generate a detailed Seedream 4.5 prompt using only Grok Vision (fast).
        Skips slow Replicate models for quick results.
        """
        image_path = await self.resolve_image_path(image_input)
        if not image_path:
            return {"status": "error", "error": f"Could not resolve image: {image_input}"}
        
        grok_result = await self.analyze_with_grok_vision(image_path)
        
        if grok_result.get("status") != "success":
            return grok_result
        
        grok_analysis = grok_result.get("analysis", "")
        detailed_prompt = self._build_detailed_seedream_prompt(grok_analysis, persona)
        
        return {
            "status": "success",
            "source_image": image_path,
            "original_input": image_input,
            "persona": persona,
            "prompt": detailed_prompt,
            "raw_analysis": {
                "grok_vision": grok_analysis
            },
            "generation_ready": True,
            "method": "grok_fast"
        }
    
    async def generate_seedream_prompt(
        self,
        image_input: str,
        persona: str = "starbright_monroe"
    ) -> Dict[str, Any]:
        """
        Generate an optimized prompt for Seedream 4.5 from a competitor image.
        
        Accepts both local file paths and URLs.
        Returns a structured prompt ready for generation.
        """
        analysis = await self.full_analysis(image_input, include_clip=True, include_grok=True)
        
        if analysis.get("status") != "success":
            return analysis
        
        resolved_path = analysis.get("image", image_input)
        
        prompt_data = {
            "status": "success",
            "source_image": resolved_path,
            "original_input": analysis.get("original_input", image_input),
            "persona": persona,
            "prompt": analysis.get("combined_prompt", ""),
            "raw_analysis": {
                "cogvlm": analysis.get("cogvlm"),
                "clip_interrogator": analysis.get("clip_interrogator"),
                "grok_vision": analysis.get("grok_vision")
            },
            "generation_ready": True
        }
        
        return prompt_data


prompt_intelligence_service = PromptIntelligenceService()
