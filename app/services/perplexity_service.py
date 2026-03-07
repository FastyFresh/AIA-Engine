"""
Perplexity Search Service for X Growth Optimization
Provides real-time trending hashtags, competitor research, and caption assistance
"""

import os
import httpx
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

class PerplexityService:
    """
    Perplexity AI search for social media growth optimization.
    
    Search Modes:
    - concise: Quick facts, trending hashtags (cheap, fast)
    - copilot: Complex reasoning, caption writing
    - deep_research: Comprehensive analysis (expensive, thorough)
    """
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not configured")
    
    async def search(
        self,
        query: str,
        mode: str = "concise",
        model: str = "sonar",
        system_prompt: Optional[str] = None
    ) -> Dict:
        """
        Execute Perplexity search with specified mode.
        
        Args:
            query: Search query
            mode: concise|copilot|deep_research
            model: sonar|sonar-pro|sonar-reasoning-pro
            system_prompt: Optional system instructions
        
        Returns:
            Dict with answer, citations, and metadata
        """
        if not self.api_key:
            return {"error": "PERPLEXITY_API_KEY not configured"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Map modes to Perplexity parameters
        mode_config = {
            "concise": {"temperature": 0.2, "max_tokens": 500},
            "copilot": {"temperature": 0.7, "max_tokens": 1000},
            "deep_research": {"temperature": 0.5, "max_tokens": 2000}
        }
        
        config = mode_config.get(mode, mode_config["concise"])
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": config["temperature"],
            "max_tokens": config["max_tokens"]
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    PERPLEXITY_API_URL,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "answer": data["choices"][0]["message"]["content"],
                        "citations": data.get("citations", []),
                        "model": model,
                        "mode": mode,
                        "tokens_used": data.get("usage", {}).get("total_tokens", 0)
                    }
                else:
                    logger.error(f"Perplexity API error: {response.status_code}")
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Perplexity search failed: {e}")
            return {"error": str(e)}
    
    # ===== X GROWTH SPECIFIC METHODS =====
    
    async def get_trending_hashtags(self) -> Dict:
        """Get trending hashtags for today (concise + sonar)"""
        query = "What hashtags are trending on X Twitter today for lifestyle, fashion, and influencer content? List the top 10 most engaging."
        
        return await self.search(
            query=query,
            mode="concise",
            model="sonar",
            system_prompt="You are a social media expert. Provide only the hashtag list, no fluff."
        )
    
    async def get_daily_trends(self, niche: str = "influencer") -> Dict:
        """Get what's trending in the creator economy today"""
        query = f"What's trending in the {niche} and creator economy on X today? What topics are getting high engagement?"
        
        return await self.search(
            query=query,
            mode="concise",
            model="sonar",
            system_prompt="You are a social media strategist. Focus on actionable trends."
        )
    
    async def research_competitors(self, competitors: List[str]) -> Dict:
        """Deep research on what top creators are posting (deep_research + sonar-pro)"""
        comp_str = ", ".join(competitors)
        query = f"What are top creators {comp_str} posting on X this week? Analyze their caption styles, hashtags, posting times, and engagement strategies. What content is performing best?"
        
        return await self.search(
            query=query,
            mode="deep_research",
            model="sonar-pro",
            system_prompt="You are a competitive intelligence analyst. Provide detailed strategic insights."
        )
    
    async def generate_captions(
        self,
        image_description: str,
        time_of_day: str,
        tone: str = "flirty",
        count: int = 3
    ) -> Dict:
        """Generate caption options (copilot + sonar-pro)"""
        query = f"""Write {count} {tone} Instagram/X captions for this image: {image_description}
        
Context:
- Time of day: {time_of_day}
- Target: males 20-65
- Tone: {tone}, casual, authentic
- Include engagement hook (question or CTA)
- Soft mention of "link in bio" or "see more"

Format as numbered list."""
        
        return await self.search(
            query=query,
            mode="copilot",
            model="sonar-pro",
            system_prompt="You are a social media copywriter specializing in influencer content. Write captions that feel natural and engaging."
        )
    
    async def optimize_hashtags(
        self,
        caption: str,
        max_tags: int = 7
    ) -> Dict:
        """Get optimized hashtag set for a caption"""
        query = f"""Given this caption: "{caption}"

Recommend {max_tags} hashtags that will maximize reach and engagement on X/Instagram.
Mix of:
- Broad trending tags
- Niche-specific tags
- Community tags

Format as space-separated list."""
        
        return await self.search(
            query=query,
            mode="concise",
            model="sonar",
            system_prompt="You are a hashtag optimization expert. Provide only the hashtag list."
        )
    
    async def get_best_posting_times(self) -> Dict:
        """Research optimal posting times"""
        query = "What are the best times to post on X (Twitter) for maximum engagement in 2026? For lifestyle/influencer content targeting US audience."
        
        return await self.search(
            query=query,
            mode="concise",
            model="sonar",
            system_prompt="You are a social media timing expert. Give specific times with reasoning."
        )
    
    async def viral_content_analysis(self, post_url: str) -> Dict:
        """Analyze why a post went viral"""
        query = f"Analyze this viral post: {post_url}. Why did it perform well? What made it engaging? What can we learn from it?"
        
        return await self.search(
            query=query,
            mode="deep_research",
            model="sonar-pro",
            system_prompt="You are a viral content analyst. Break down the psychology and mechanics of engagement."
        )

# Singleton instance
perplexity_service = PerplexityService()
