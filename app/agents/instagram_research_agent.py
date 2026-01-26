"""
Instagram Research Agent - Scrapes and analyzes successful AI influencers
to generate optimized prompts for content creation.

Uses Apify Instagram Scraper API to extract:
- Profile info (followers, bio, engagement)
- Posts (images, captions, likes, comments)
- Content patterns (poses, outfits, settings, caption hooks)

Then uses Grok to analyze patterns and generate prompts tailored for our personas.
"""
import os
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")


class InstagramResearchAgent:
    """
    Scrapes and analyzes Instagram profiles to extract content strategies
    and generate optimized prompts for AI influencer content.
    
    Now with Grok Vision for actual image analysis!
    """
    
    # Body type definitions for strict enforcement
    BODY_TYPE_DEFINITIONS = {
        "starbright_monroe": {
            "required_terms": [
                "extremely thin", "slender", "very narrow waist", "slim hips",
                "petite", "size 0", "delicate frame"
            ],
            "forbidden_terms": [
                "curvy", "voluptuous", "hourglass", "thick", "full figure",
                "wide hips", "big", "large", "busty", "ample"
            ],
            "body_description": (
                "extremely thin slender body with very narrow tiny waist, "
                "slim straight hips, small petite rear, long thin slender legs, "
                "delicate petite size 0 frame"
            ),
            "enforcement_note": (
                "CRITICAL: This persona has an extremely thin, almost boyish figure. "
                "Do NOT add curves, do NOT make her curvy or voluptuous. "
                "She should look like a slim fashion model, not a glamour model."
            )
        },
        "luna_vale": {
            "required_terms": [
                "slim", "petite", "slender", "pink hair"
            ],
            "forbidden_terms": [
                "olive skin", "dark hair", "athletic", "toned"
            ],
            "body_description": "fair pale skin with light freckles, slim petite build, long pink hair, blue eyes",
            "enforcement_note": "Slim petite fashion model with distinctive pink hair and fair skin with freckles."
        }
    }
    
    def __init__(self):
        self.apify_token = APIFY_API_TOKEN
        self.xai_key = XAI_API_KEY
        self.cache_dir = Path("content/research_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = Path("content/research_images")
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.prompt_library_path = Path("content/prompt_library.json")
    
    def enforce_body_type(self, prompt: str, persona_id: str = "starbright_monroe") -> str:
        """
        Post-process a prompt to enforce body type constraints.
        Removes forbidden terms and ensures required body description is present.
        """
        body_def = self.BODY_TYPE_DEFINITIONS.get(persona_id, {})
        if not body_def:
            return prompt
        
        # Remove forbidden terms
        modified_prompt = prompt
        for term in body_def.get("forbidden_terms", []):
            # Case-insensitive replacement
            import re
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            modified_prompt = pattern.sub("slim", modified_prompt)
        
        # Check if body description is present, add if missing
        body_desc = body_def.get("body_description", "")
        has_body_terms = any(
            term.lower() in modified_prompt.lower() 
            for term in body_def.get("required_terms", [])[:3]  # Check first 3 required terms
        )
        
        if not has_body_terms and body_desc:
            # Insert body description after the first sentence or at the start
            if ". " in modified_prompt:
                parts = modified_prompt.split(". ", 1)
                modified_prompt = f"{parts[0]}. She has {body_desc}. {parts[1]}"
            else:
                modified_prompt = f"She has {body_desc}. {modified_prompt}"
        
        return modified_prompt
    
    def validate_prompt_body_type(self, prompt: str, persona_id: str = "starbright_monroe") -> Dict:
        """
        Validate a prompt for body type consistency.
        Returns validation result with issues if any.
        """
        body_def = self.BODY_TYPE_DEFINITIONS.get(persona_id, {})
        if not body_def:
            return {"valid": True, "issues": []}
        
        issues = []
        
        # Check for forbidden terms
        for term in body_def.get("forbidden_terms", []):
            if term.lower() in prompt.lower():
                issues.append(f"Contains forbidden body term: '{term}'")
        
        # Check for required terms
        required_found = sum(
            1 for term in body_def.get("required_terms", [])
            if term.lower() in prompt.lower()
        )
        if required_found < 2:
            issues.append("Missing body type descriptors - may not enforce thin body type")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "required_terms_found": required_found
        }
        
    async def scrape_profile(self, username: str, posts_limit: int = 30) -> Dict:
        """
        Scrape Instagram profile and recent posts using Apify.
        
        Args:
            username: Instagram username (without @)
            posts_limit: Number of posts to scrape
            
        Returns:
            Dict with profile info and posts data
        """
        if not self.apify_token:
            return {
                "success": False,
                "error": "APIFY_API_TOKEN not configured. Please add it to your secrets."
            }
        
        # Clean username - handle full URLs and @ symbols
        username = username.replace("@", "").strip()
        # Extract username from Instagram URLs
        if "instagram.com/" in username:
            # Handle https://www.instagram.com/username/ or instagram.com/username
            parts = username.split("instagram.com/")
            if len(parts) > 1:
                username = parts[1].strip("/").split("/")[0].split("?")[0]
        username = username.strip()
        
        cache_file = self.cache_dir / f"{username}_profile.json"
        if cache_file.exists():
            cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            if cache_age < 86400:
                logger.info(f"Using cached data for @{username}")
                with open(cache_file) as f:
                    return json.load(f)
        
        logger.info(f"Scraping Instagram profile: @{username}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                run_input = {
                    "directUrls": [f"https://www.instagram.com/{username}/"],
                    "resultsLimit": posts_limit,
                    "resultsType": "posts"
                }
                
                start_response = await client.post(
                    "https://api.apify.com/v2/acts/apify~instagram-scraper/runs",
                    headers={"Authorization": f"Bearer {self.apify_token}"},
                    json=run_input
                )
                
                if start_response.status_code != 201:
                    return {
                        "success": False,
                        "error": f"Failed to start scraper: {start_response.text}"
                    }
                
                run_data = start_response.json()
                run_id = run_data["data"]["id"]
                
                logger.info(f"Apify run started: {run_id}")
                
                for attempt in range(60):
                    await asyncio.sleep(5)
                    
                    status_response = await client.get(
                        f"https://api.apify.com/v2/acts/apify~instagram-scraper/runs/{run_id}",
                        headers={"Authorization": f"Bearer {self.apify_token}"}
                    )
                    
                    status = status_response.json()["data"]["status"]
                    
                    if status == "SUCCEEDED":
                        break
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        return {
                            "success": False,
                            "error": f"Scraper run failed with status: {status}"
                        }
                else:
                    return {
                        "success": False,
                        "error": "Scraper timed out after 5 minutes"
                    }
                
                dataset_id = run_data["data"]["defaultDatasetId"]
                items_response = await client.get(
                    f"https://api.apify.com/v2/datasets/{dataset_id}/items",
                    headers={"Authorization": f"Bearer {self.apify_token}"}
                )
                
                items = items_response.json()
                
                result = {
                    "success": True,
                    "username": username,
                    "scraped_at": datetime.now().isoformat(),
                    "posts_count": len(items),
                    "posts": items
                }
                
                with open(cache_file, "w") as f:
                    json.dump(result, f, indent=2)
                
                logger.info(f"Scraped {len(items)} posts from @{username}")
                return result
                
        except Exception as e:
            logger.error(f"Scrape error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_post_images(self, scraped_data: Dict, max_images: int = 10) -> List[str]:
        """
        Download images from scraped posts for vision analysis.
        
        Returns list of local file paths to downloaded images.
        """
        if not scraped_data.get("success"):
            return []
        
        posts = scraped_data.get("posts", [])
        username = scraped_data.get("username", "unknown")
        
        user_images_dir = self.images_dir / username
        user_images_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_paths = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, post in enumerate(posts[:max_images]):
                if post.get("isVideo", False):
                    continue
                
                image_url = post.get("displayUrl")
                if not image_url:
                    continue
                
                try:
                    response = await client.get(image_url)
                    if response.status_code == 200:
                        image_path = user_images_dir / f"post_{i+1}.jpg"
                        with open(image_path, "wb") as f:
                            f.write(response.content)
                        downloaded_paths.append(str(image_path))
                        logger.info(f"Downloaded image {i+1} from @{username}")
                except Exception as e:
                    logger.warning(f"Failed to download image {i+1}: {e}")
                    continue
        
        logger.info(f"Downloaded {len(downloaded_paths)} images from @{username}")
        return downloaded_paths
    
    async def analyze_images_with_vision(self, image_paths: List[str], username: str) -> Dict:
        """
        Use Grok Vision to analyze downloaded images and extract visual patterns.
        
        Returns detailed analysis of poses, outfits, settings, expressions.
        """
        if not image_paths:
            return {
                "success": False,
                "error": "No images to analyze"
            }
        
        if not self.xai_key:
            return {
                "success": False,
                "error": "XAI_API_KEY not configured"
            }
        
        import base64
        
        all_analyses = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, image_path in enumerate(image_paths[:10]):
                try:
                    with open(image_path, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode("utf-8")
                    
                    logger.info(f"Analyzing image {i+1}/{len(image_paths)} with Grok Vision...")
                    
                    response = await client.post(
                        "https://api.x.ai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.xai_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "grok-2-vision-latest",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{image_data}"
                                            }
                                        },
                                        {
                                            "type": "text",
                                            "text": """Analyze this influencer photo in detail. Describe:

1. POSE: Exact body position, hand placement, stance, angle to camera
2. EXPRESSION: Facial expression, eye direction, mood conveyed
3. OUTFIT: Specific clothing items, colors, style, fit, revealing level (1-10)
4. SETTING: Location, background elements, props visible
5. LIGHTING: Type, direction, mood
6. COMPOSITION: Framing, crop style (full body, upper body, portrait)
7. OVERALL VIBE: The mood/aesthetic being conveyed

Be specific and detailed. This is for creating similar content."""
                                        }
                                    ]
                                }
                            ],
                            "temperature": 0.3,
                            "max_tokens": 800
                        }
                    )
                    
                    if response.status_code == 200:
                        analysis = response.json()["choices"][0]["message"]["content"]
                        all_analyses.append({
                            "image_num": i + 1,
                            "path": image_path,
                            "analysis": analysis
                        })
                        logger.info(f"Successfully analyzed image {i+1}")
                    else:
                        logger.warning(f"Vision API error for image {i+1}: {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"Failed to analyze image {i+1}: {e}")
                    continue
        
        if not all_analyses:
            return {
                "success": False,
                "error": "Failed to analyze any images"
            }
        
        combined_analysis = "\n\n---\n\n".join([
            f"IMAGE {a['image_num']}:\n{a['analysis']}" 
            for a in all_analyses
        ])
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.xai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-3-latest",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are analyzing influencer content patterns. Synthesize the individual image analyses into patterns."
                            },
                            {
                                "role": "user",
                                "content": f"""Based on these {len(all_analyses)} image analyses from @{username}, identify the consistent patterns:

{combined_analysis}

Synthesize into JSON format:
{{
    "pose_patterns": ["list of common poses observed"],
    "expression_patterns": ["list of common expressions/looks"],
    "outfit_patterns": ["list of common outfit types and styles"],
    "setting_patterns": ["list of common locations/backgrounds"],
    "lighting_patterns": ["list of lighting styles used"],
    "composition_patterns": ["list of framing/crop styles"],
    "revealing_level_avg": "average revealing level 1-10",
    "overall_aesthetic": "description of the overall visual brand",
    "key_elements_for_recreation": ["top 5 elements to replicate for similar content"]
}}"""
                            }
                        ],
                        "temperature": 0.3
                    }
                )
                
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    patterns = json.loads(content.strip())
                    
                    return {
                        "success": True,
                        "username": username,
                        "images_analyzed": len(all_analyses),
                        "individual_analyses": all_analyses,
                        "patterns": patterns,
                        "analyzed_at": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Pattern synthesis error: {e}")
        
        return {
            "success": True,
            "username": username,
            "images_analyzed": len(all_analyses),
            "individual_analyses": all_analyses,
            "patterns": None,
            "analyzed_at": datetime.now().isoformat()
        }
    
    async def analyze_content_patterns(self, scraped_data: Dict) -> Dict:
        """
        Use Grok to analyze scraped content and extract patterns.
        
        Returns analysis of:
        - Pose patterns
        - Outfit patterns  
        - Setting/background patterns
        - Caption hooks and engagement strategies
        - Visual style notes
        """
        if not scraped_data.get("success"):
            return scraped_data
        
        if not self.xai_key:
            return {
                "success": False,
                "error": "XAI_API_KEY not configured"
            }
        
        posts = scraped_data.get("posts", [])[:20]
        
        posts_summary = []
        for i, post in enumerate(posts):
            caption = post.get("caption", "")[:500] if post.get("caption") else ""
            posts_summary.append({
                "post_num": i + 1,
                "caption": caption,
                "likes": post.get("likesCount", 0),
                "comments": post.get("commentsCount", 0),
                "type": post.get("type", "image"),
                "is_video": post.get("isVideo", False)
            })
        
        analysis_prompt = f"""Analyze this Instagram influencer's content and extract patterns ONLY from what is explicitly mentioned in their captions.

CRITICAL RULES:
- DO NOT invent or assume visual content you cannot see
- DO NOT add "futuristic", "cyberpunk", "neon", or sci-fi themes unless EXPLICITLY mentioned in captions
- ONLY extract patterns that are DIRECTLY stated or clearly implied in the caption text
- For visual patterns, write "not specified in captions" if the captions don't describe outfits/poses/settings
- Focus on caption hooks, engagement strategies, and text patterns you can actually observe

Username: @{scraped_data.get('username')}
Posts analyzed: {len(posts_summary)}

POST DATA:
{json.dumps(posts_summary, indent=2)}

Provide a grounded analysis in JSON format:

{{
    "profile_summary": {{
        "estimated_niche": "based on caption language and hashtags",
        "content_style": "based on caption tone only",
        "engagement_strategy": "how they drive engagement"
    }},
    "caption_patterns": {{
        "hooks": ["EXACT caption hook formulas from the data"],
        "ctas": ["EXACT call-to-action phrases from captions"],
        "emoji_usage": "observed emoji patterns",
        "length": "typical caption length"
    }},
    "visual_patterns": {{
        "mentioned_outfits": ["outfits ONLY if mentioned in captions, otherwise empty"],
        "mentioned_settings": ["locations ONLY if mentioned in captions, otherwise empty"],
        "style_keywords": ["style words from captions like 'cozy', 'glam', etc."]
    }},
    "engagement_hooks": {{
        "question_formats": ["EXACT question templates from captions"],
        "opinion_prompts": ["EXACT yay/nay prompts from captions"],
        "interaction_triggers": ["observed patterns that get comments"]
    }},
    "top_performing_content": {{
        "highest_engagement_themes": ["themes from highest engagement posts"],
        "common_words": ["frequently used descriptive words in captions"]
    }}
}}

Be factual. Only report what you can observe in the caption text. Do not speculate about visuals."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.xai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-3-latest",
                        "messages": [
                            {"role": "system", "content": "You are an expert social media analyst. Only report patterns you can directly observe in the provided data. Do not invent or assume visual content. Respond only with valid JSON."},
                            {"role": "user", "content": analysis_prompt}
                        ],
                        "temperature": 0.3
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Grok API error: {response.text}"
                    }
                
                content = response.json()["choices"][0]["message"]["content"]
                
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                analysis = json.loads(content.strip())
                
                return {
                    "success": True,
                    "username": scraped_data.get("username"),
                    "analysis": analysis,
                    "posts_analyzed": len(posts_summary),
                    "analyzed_at": datetime.now().isoformat()
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Grok response: {e}")
            return {
                "success": False,
                "error": f"Failed to parse analysis: {e}"
            }
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_prompts_from_analysis(
        self, 
        analysis: Dict, 
        persona_name: str = "Starbright Monroe",
        persona_description: str = "pale ivory skin, slim athletic figure, dark brown hair, warm olive brown eyes",
        num_prompts: int = 15
    ) -> Dict:
        """
        Generate image generation prompts based on analyzed patterns.
        
        Tailors prompts to the specific persona while following
        successful patterns from the analyzed influencer.
        """
        if not analysis.get("success"):
            return analysis
        
        if not self.xai_key:
            return {
                "success": False,
                "error": "XAI_API_KEY not configured"
            }
        
        patterns = analysis.get("analysis", {})
        
        prompt_request = f"""Generate {num_prompts} image generation prompts for our persona based on the analyzed patterns.

CRITICAL RULES - DO NOT VIOLATE:
- DO NOT use futuristic, cyberpunk, neon, holographic, or sci-fi themes
- DO NOT add technology, metallic, or high-tech elements
- Use ONLY realistic, everyday settings: apartments, bedrooms, bathrooms, gyms, pools, beaches, cafes, rooftops
- Use ONLY realistic outfits: loungewear, dresses, swimwear, activewear, casual wear, evening gowns
- Focus on lifestyle, glamour, intimate, and natural settings
- Keep lighting natural or cinematic - no neon/colored lighting unless source data mentions it

ANALYZED PATTERNS:
{json.dumps(patterns, indent=2)}

OUR PERSONA:
Name: {persona_name}
Physical: {persona_description}
Style: Hyperrealistic, natural beauty, elegant, confident

REQUIREMENTS:
1. Each prompt should describe a realistic lifestyle photo
2. Include specific pose, outfit, realistic setting, natural lighting
3. Vary categories: intimate (bedroom/bathroom), glamour (evening wear), casual (lifestyle), fitness, portrait
4. Make prompts safe for mainstream AI image generators
5. Include the persona's physical characteristics

Generate prompts in this JSON format:
{{
    "prompts": [
        {{
            "id": 1,
            "category": "intimate/glamour/casual/fitness/portrait",
            "prompt": "full image generation prompt here",
            "caption_hook": "suggested caption hook for this image",
            "engagement_question": "yay/nay style question"
        }}
    ]
}}

Keep prompts grounded in reality. Think lifestyle influencer, not sci-fi model."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.xai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-3-latest",
                        "messages": [
                            {"role": "system", "content": "You are a lifestyle photographer creating realistic influencer photo concepts. Never use futuristic, cyberpunk, or sci-fi themes. Keep everything grounded in real-world settings. Respond only with valid JSON."},
                            {"role": "user", "content": prompt_request}
                        ],
                        "temperature": 0.5
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Grok API error: {response.text}"
                    }
                
                content = response.json()["choices"][0]["message"]["content"]
                
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                prompts_data = json.loads(content.strip())
                
                return {
                    "success": True,
                    "persona": persona_name,
                    "source_influencer": analysis.get("username"),
                    "prompts": prompts_data.get("prompts", []),
                    "generated_at": datetime.now().isoformat()
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse prompt response: {e}")
            return {
                "success": False,
                "error": f"Failed to parse prompts: {e}"
            }
        except Exception as e:
            logger.error(f"Prompt generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_prompts_from_visual_analysis(
        self,
        visual_analysis: Dict,
        persona_name: str = "Starbright Monroe",
        persona_id: str = "starbright_monroe",
        persona_description: str = "extremely thin slender body, very narrow waist, slim hips, long slender legs, petite delicate frame, pale ivory skin, warm olive brown eyes, long dark brown hair",
        num_prompts: int = 15
    ) -> Dict:
        """
        Generate prompts based on actual visual analysis from Grok Vision.
        Includes body type enforcement to ensure generated prompts maintain persona consistency.
        """
        if not visual_analysis.get("success"):
            return visual_analysis
        
        if not self.xai_key:
            return {"success": False, "error": "XAI_API_KEY not configured"}
        
        patterns = visual_analysis.get("patterns", {})
        individual = visual_analysis.get("individual_analyses", [])
        
        individual_text = "\n\n".join([
            f"Image {a['image_num']}: {a['analysis'][:500]}..." 
            for a in individual[:5]
        ])
        
        # Get body type enforcement rules
        body_def = self.BODY_TYPE_DEFINITIONS.get(persona_id, {})
        body_enforcement = body_def.get("enforcement_note", "")
        forbidden_terms = body_def.get("forbidden_terms", [])
        
        prompt_request = f"""Generate {num_prompts} image generation prompts for our persona based on ACTUAL visual patterns observed in competitor images.

VISUAL PATTERNS OBSERVED:
{json.dumps(patterns, indent=2) if patterns else "No patterns synthesized"}

SAMPLE IMAGE DESCRIPTIONS:
{individual_text}

OUR PERSONA:
Name: {persona_name}
Physical: {persona_description}
Style: Hyperrealistic, provocative yet tasteful, confident, alluring

*** BODY TYPE ENFORCEMENT - CRITICAL ***
{body_enforcement}
Every prompt MUST include the body description: "{persona_description}"
FORBIDDEN TERMS - DO NOT USE: {', '.join(forbidden_terms) if forbidden_terms else 'none'}
The persona's body type must be explicitly stated in each prompt to ensure image generation maintains consistency.

CRITICAL REQUIREMENTS:
1. MATCH the poses, outfits, and settings observed in the analyzed images
2. Maintain the same revealing level and provocative style
3. ALWAYS include the full body description in each prompt
4. Include specific details: exact pose, outfit description, setting, lighting, expression
5. Each prompt should recreate the successful patterns observed
6. Categories: intimate, glamour, casual, fitness, portrait

SAFETY TRANSFORMS (apply these):
- Use "loungewear" instead of "lingerie"
- Use "swimwear" instead of "bikini"  
- Use "curves" instead of "buttocks"
- Use "fitted" instead of "tight"

Generate JSON format:
{{
    "prompts": [
        {{
            "id": 1,
            "category": "intimate/glamour/casual/fitness/portrait",
            "prompt": "detailed image generation prompt - MUST include body type description",
            "source_pattern": "which observed pattern this recreates"
        }}
    ]
}}"""

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.xai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-3-latest",
                        "messages": [
                            {"role": "system", "content": f"You are creating image generation prompts that replicate successful influencer content patterns. Be specific about poses, outfits, and settings. Match the provocative style while using safe language. CRITICAL: Every prompt must include the exact body type description to ensure the AI generates the correct physique. {body_enforcement}"},
                            {"role": "user", "content": prompt_request}
                        ],
                        "temperature": 0.5
                    }
                )
                
                if response.status_code != 200:
                    return {"success": False, "error": f"Grok API error: {response.text}"}
                
                content = response.json()["choices"][0]["message"]["content"]
                
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                prompts_data = json.loads(content.strip())
                raw_prompts = prompts_data.get("prompts", [])
                
                # Post-process: Enforce body type on each generated prompt
                enforced_prompts = []
                for p in raw_prompts:
                    original_prompt = p.get("prompt", "")
                    enforced_prompt = self.enforce_body_type(original_prompt, persona_id)
                    validation = self.validate_prompt_body_type(enforced_prompt, persona_id)
                    
                    enforced_prompts.append({
                        **p,
                        "prompt": enforced_prompt,
                        "body_type_enforced": original_prompt != enforced_prompt,
                        "body_type_valid": validation.get("valid", False)
                    })
                
                logger.info(f"Generated {len(enforced_prompts)} prompts with body type enforcement")
                
                return {
                    "success": True,
                    "persona": persona_name,
                    "persona_id": persona_id,
                    "prompts": enforced_prompts,
                    "based_on_images": visual_analysis.get("images_analyzed", 0),
                    "body_type_enforced": True,
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Visual prompt generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def full_research_pipeline(
        self,
        username: str,
        persona_name: str = "Starbright Monroe",
        persona_id: str = "starbright_monroe",
        persona_description: str = "extremely thin slender body, very narrow waist, slim hips, long slender legs, petite delicate frame, pale ivory skin, warm olive brown eyes, long dark brown hair",
        posts_limit: int = 30,
        num_prompts: int = 15
    ) -> Dict:
        """
        Run the complete research pipeline with VISUAL ANALYSIS:
        1. Scrape Instagram profile
        2. Download post images
        3. Analyze images with Grok Vision
        4. Generate prompts based on actual visual content
        """
        logger.info(f"Starting research pipeline for @{username}")
        
        scraped = await self.scrape_profile(username, posts_limit)
        if not scraped.get("success"):
            return scraped
        
        posts = scraped.get("posts", [])
        has_images = any(post.get("displayUrl") for post in posts if not post.get("error"))
        
        if has_images:
            logger.info(f"Downloading images from @{username} for visual analysis...")
            image_paths = await self.download_post_images(scraped, max_images=10)
            
            if image_paths:
                logger.info(f"Analyzing {len(image_paths)} images with Grok Vision...")
                visual_analysis = await self.analyze_images_with_vision(image_paths, username)
                
                if visual_analysis.get("success") and visual_analysis.get("patterns"):
                    logger.info("Generating prompts from visual analysis...")
                    prompts = await self.generate_prompts_from_visual_analysis(
                        visual_analysis,
                        persona_name=persona_name,
                        persona_id=persona_id,
                        persona_description=persona_description,
                        num_prompts=num_prompts
                    )
                    
                    result = {
                        "success": True,
                        "username": username,
                        "analysis_type": "visual",
                        "profile_data": {
                            "posts_scraped": scraped.get("posts_count", 0),
                            "images_analyzed": visual_analysis.get("images_analyzed", 0),
                            "scraped_at": scraped.get("scraped_at")
                        },
                        "visual_patterns": visual_analysis.get("patterns"),
                        "prompts": prompts.get("prompts", []),
                        "generated_at": datetime.now().isoformat()
                    }
                    
                    self.save_to_prompt_library(result)
                    return result
        
        logger.info("Falling back to caption-based analysis...")
        analysis = await self.analyze_content_patterns(scraped)
        if not analysis.get("success"):
            return analysis
        
        prompts = await self.generate_prompts_from_analysis(
            analysis,
            persona_name=persona_name,
            persona_description=persona_description,
            num_prompts=num_prompts
        )
        
        result = {
            "success": True,
            "username": username,
            "analysis_type": "caption_only",
            "profile_data": {
                "posts_scraped": scraped.get("posts_count", 0),
                "scraped_at": scraped.get("scraped_at")
            },
            "analysis": analysis.get("analysis"),
            "prompts": prompts.get("prompts", []),
            "generated_at": datetime.now().isoformat()
        }
        
        self.save_to_prompt_library(result)
        
        return result
    
    def save_to_prompt_library(self, research_result: Dict):
        """Save generated prompts to the prompt library."""
        library = self.load_prompt_library()
        
        source = research_result.get("username", "unknown")
        prompts = research_result.get("prompts", [])
        
        if source not in library:
            library[source] = {
                "added_at": datetime.now().isoformat(),
                "prompts": []
            }
        
        for prompt in prompts:
            prompt["source_influencer"] = source
            prompt["added_at"] = datetime.now().isoformat()
            library[source]["prompts"].append(prompt)
        
        with open(self.prompt_library_path, "w") as f:
            json.dump(library, f, indent=2)
        
        logger.info(f"Saved {len(prompts)} prompts to library from @{source}")
    
    def load_prompt_library(self) -> Dict:
        """Load the prompt library."""
        if self.prompt_library_path.exists():
            with open(self.prompt_library_path) as f:
                return json.load(f)
        return {}
    
    def get_prompts_by_category(self, category: str = None) -> List[Dict]:
        """Get prompts from library, optionally filtered by category. Returns newest first."""
        library = self.load_prompt_library()
        all_prompts = []
        global_id = 1
        
        for source, data in library.items():
            for prompt in data.get("prompts", []):
                prompt_copy = prompt.copy()
                prompt_copy["source"] = source
                prompt_copy["id"] = global_id
                global_id += 1
                if category is None or prompt_copy.get("category") == category:
                    all_prompts.append(prompt_copy)
        
        # Sort by added_at timestamp (newest first)
        all_prompts.sort(key=lambda x: x.get("added_at", ""), reverse=True)
        
        return all_prompts
    
    def get_engagement_hooks(self) -> List[Dict]:
        """Get all caption hooks and engagement questions from library."""
        library = self.load_prompt_library()
        hooks = []
        
        for source, data in library.items():
            for prompt in data.get("prompts", []):
                if prompt.get("caption_hook") or prompt.get("engagement_question"):
                    hooks.append({
                        "source": source,
                        "caption_hook": prompt.get("caption_hook"),
                        "engagement_question": prompt.get("engagement_question"),
                        "category": prompt.get("category")
                    })
        
        return hooks


instagram_research_agent = InstagramResearchAgent()
