"""
DFans CTA Optimizer Agent
Boosts X → DFans conversion via optimized CTAs, pinned posts, and bio updates.
Uses Grok AI to generate persona-appropriate suggestions.
"""

import os
import httpx
import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

XAI_API_KEY = os.environ.get("XAI_API_KEY")
XAI_BASE_URL = "https://api.x.ai/v1"

PERSONA_CONFIG = {
    "starbright_monroe": {
        "name": "Starbright",
        "handle": "@Starbright2003",
        "dfans_url": "dfans.co/starbrightnight",
        "tone": "warm, direct, lightly flirty, confident",
        "audience": "men ages 20-60",
        "style": "playful but not desperate, soft tease, mischievous",
        "emoji_style": "minimal - white heart 🤍, sparkle ✨, soft blush occasional"
    },
    "luna_vale": {
        "name": "Luna",
        "handle": "@LunaVale",
        "dfans_url": "dfans.co/lunavale",
        "tone": "sweet, playful, natural",
        "audience": "men ages 20-40",
        "style": "cute, approachable, girl-next-door",
        "emoji_style": "playful - hearts, sparkles"
    }
}

CTA_TEMPLATES = {
    "soft_tease": [
        "more of this energy behind the link ↓",
        "this is just the preview ✨",
        "the good stuff is waiting for you",
        "want to see what happens next?",
        "there's more where this came from 🤍",
        "you're not ready for what's on my page",
        "I saved the best for somewhere else ↓"
    ],
    "curiosity": [
        "come find out what I'm really like",
        "I don't show everything here...",
        "some things are just between us",
        "the real me is behind that link",
        "I'm more fun when we're alone ✨"
    ],
    "direct": [
        "link in bio 🤍",
        "you know where to find me",
        "come say hi ↓",
        "let's chat somewhere more private"
    ],
    "exclusive": [
        "exclusive content waiting for you",
        "join me for the uncensored version",
        "my subscribers get the real content",
        "VIP access in my bio ↓"
    ]
}

BIO_TEMPLATES = [
    "{name} ✨ | Your favorite distraction | {dfans_cta}",
    "{name} 🤍 | Making your day a little brighter | {dfans_cta}",
    "{name} | Content creator | The good stuff → {dfans_url}",
    "Just a girl living her best life ✨ | {name} | {dfans_cta}",
    "{name} | I post the previews here 🤍 | Full content ↓"
]

PINNED_POST_HOOKS = [
    "Hi, I'm {name} 🤍 If you're new here, welcome! I share a little bit of everything - but my best content is on DFans. Come say hi?",
    "POV: You just found your new favorite page ✨ I'm {name}, and I'd love for you to join me. Link below.",
    "New here? I'm {name}! I post previews on X but the real content lives somewhere else... 🤍 You know what to do ↓",
    "Thanks for stopping by! I'm {name} - creator, model, and your new obsession (maybe?) ✨ See the rest on DFans"
]


class FanvueCTAOptimizer:
    """
    Generates optimized CTAs, bio suggestions, and pinned post content
    to maximize X → DFans conversions.
    """
    
    def __init__(self, persona: str = "starbright_monroe"):
        self.persona = persona
        self.config = PERSONA_CONFIG.get(persona, PERSONA_CONFIG["starbright_monroe"])
        self.cta_rotation_index = 0
        logger.info(f"FanvueCTAOptimizer initialized for {self.config['name']}")
    
    async def optimize_all(self, post_metrics: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Generate all optimization suggestions at once.
        
        Args:
            post_metrics: Recent post performance data (optional)
        
        Returns:
            Complete optimization package
        """
        return {
            "suggested_bio": await self.generate_bio_suggestion(),
            "suggested_pinned_post": await self.generate_pinned_post(),
            "cta_templates": self.get_cta_library(),
            "post_cta": self.get_next_cta(),
            "optimization_tips": self._get_optimization_tips(post_metrics),
            "generated_at": datetime.now().isoformat()
        }
    
    async def generate_bio_suggestion(self) -> Dict[str, Any]:
        """Generate AI-optimized bio suggestion using Grok"""
        
        prompt = f"""Generate a Twitter/X bio for an influencer with these characteristics:
- Name: {self.config['name']}
- Tone: {self.config['tone']}
- Target audience: {self.config['audience']}
- DFans link: {self.config['dfans_url']}

Requirements:
- Maximum 160 characters
- Include a soft CTA to DFans (no explicit language)
- Use minimal emojis (1-2 max)
- Sound natural, not salesy
- Flirty but SFW/PG-13
- Do NOT use words like "uncensored", "NSFW", "18+"

Return ONLY the bio text, nothing else."""

        try:
            if not XAI_API_KEY:
                template = random.choice(BIO_TEMPLATES)
                return {
                    "bio": template.format(
                        name=self.config['name'],
                        dfans_url=self.config['dfans_url'],
                        dfans_cta=f"More → {self.config['dfans_url']}"
                    ),
                    "source": "template",
                    "character_count": 0
                }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{XAI_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {XAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-3-latest",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 100,
                        "temperature": 0.8
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bio = data["choices"][0]["message"]["content"].strip()
                    bio = bio.strip('"\'')
                    
                    if len(bio) > 160:
                        bio = bio[:157] + "..."
                    
                    return {
                        "bio": bio,
                        "source": "grok_ai",
                        "character_count": len(bio)
                    }
                else:
                    logger.warning(f"Grok API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error generating bio: {e}")
        
        template = random.choice(BIO_TEMPLATES)
        bio = template.format(
            name=self.config['name'],
            dfans_url=self.config['dfans_url'],
            dfans_cta=f"More → {self.config['dfans_url']}"
        )
        return {"bio": bio, "source": "template", "character_count": len(bio)}
    
    async def generate_pinned_post(self) -> Dict[str, Any]:
        """Generate AI-optimized pinned post content"""
        
        prompt = f"""Write a pinned post for a Twitter/X influencer:
- Name: {self.config['name']}
- Tone: {self.config['tone']}
- Style: {self.config['style']}
- Goal: Drive traffic to DFans without being pushy

Requirements:
- 200-280 characters (Twitter limit)
- Warm, welcoming intro for new followers
- Soft mention of exclusive content on DFans
- 1-2 emojis maximum
- SFW/PG-13, no explicit keywords
- Sound authentic, not like an ad

Return ONLY the post text."""

        try:
            if not XAI_API_KEY:
                template = random.choice(PINNED_POST_HOOKS)
                return {
                    "content": template.format(name=self.config['name']),
                    "source": "template"
                }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{XAI_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {XAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-3-latest",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 150,
                        "temperature": 0.8
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    content = content.strip('"\'')
                    
                    return {
                        "content": content,
                        "source": "grok_ai",
                        "character_count": len(content)
                    }
                    
        except Exception as e:
            logger.error(f"Error generating pinned post: {e}")
        
        template = random.choice(PINNED_POST_HOOKS)
        return {
            "content": template.format(name=self.config['name']),
            "source": "template"
        }
    
    async def generate_post_cta(self, context: Optional[Dict] = None) -> str:
        """
        Generate a context-aware CTA for a specific post.
        
        Args:
            context: Optional context about the post (outfit, setting, mood)
        """
        context = context or {}
        
        prompt = f"""Generate a short CTA (call-to-action) for a social media post.

Context:
- Creator: {self.config['name']} ({self.config['tone']})
- Content type: {context.get('content_type', 'lifestyle photo/video')}
- Setting: {context.get('setting', 'casual')}
- Goal: Soft drive to DFans

Requirements:
- Maximum 50 characters
- Flirty, playful, not desperate
- No explicit language
- Can use 1 emoji max
- Should create curiosity

Return ONLY the CTA text."""

        try:
            if XAI_API_KEY:
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.post(
                        f"{XAI_BASE_URL}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {XAI_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "grok-3-latest",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 50,
                            "temperature": 0.9
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        cta = data["choices"][0]["message"]["content"].strip()
                        return cta.strip('"\'')
                        
        except Exception as e:
            logger.error(f"Error generating post CTA: {e}")
        
        return self.get_next_cta()
    
    def get_cta_library(self) -> Dict[str, List[str]]:
        """Get the full CTA template library"""
        return CTA_TEMPLATES
    
    def get_next_cta(self, category: str = "soft_tease") -> str:
        """
        Get next CTA from rotation to avoid repetition.
        
        Args:
            category: CTA category (soft_tease, curiosity, direct, exclusive)
        """
        templates = CTA_TEMPLATES.get(category, CTA_TEMPLATES["soft_tease"])
        cta = templates[self.cta_rotation_index % len(templates)]
        self.cta_rotation_index += 1
        return cta
    
    def get_random_cta(self, category: Optional[str] = None) -> str:
        """Get a random CTA, optionally from a specific category"""
        if category and category in CTA_TEMPLATES:
            return random.choice(CTA_TEMPLATES[category])
        
        all_ctas = []
        for ctas in CTA_TEMPLATES.values():
            all_ctas.extend(ctas)
        return random.choice(all_ctas)
    
    def _get_optimization_tips(self, post_metrics: Optional[List[Dict]] = None) -> List[str]:
        """Generate optimization tips based on performance data"""
        tips = [
            "Pin your best-performing post with DFans CTA",
            "Update bio weekly to keep it fresh",
            "Rotate CTAs to avoid fatigue - don't use the same one twice in a row",
            "Best posting times: 9-11 AM and 7-10 PM EST",
            "Use 'soft tease' CTAs for photos, 'curiosity' for videos"
        ]
        
        if post_metrics:
            pass
        
        return tips[:3]


cta_optimizer_starbright = FanvueCTAOptimizer("starbright_monroe")
cta_optimizer_luna = FanvueCTAOptimizer("luna_vale")


def get_optimizer(persona: str = "starbright_monroe") -> FanvueCTAOptimizer:
    """Get the appropriate CTA optimizer for a persona"""
    if persona == "luna_vale":
        return cta_optimizer_luna
    return cta_optimizer_starbright
