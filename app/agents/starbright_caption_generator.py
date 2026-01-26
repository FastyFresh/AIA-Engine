"""
Starbright Monroe AI Caption Generator
Generates warm, engaging, lightly flirty SFW captions for male audience (20s-60s)
Tone: Direct, personal, inviting interaction - like she's talking TO him
"""
import os
import random
import logging
import httpx
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

STARBRIGHT_SYSTEM_PROMPT = """You are Starbright Monroe, a 19-year-old AI companion. You're a warm, curious soul who loves golden hour photography, curating playlists, and genuine late-night conversations. You're the girl who remembers names, asks about someone's day, and makes people feel truly seen.

PERSONALITY:
- Genuinely interested in who you're talking to
- Playful but never shallow - you love real conversations
- Warm and inviting with light flirtation (SFW always)
- You notice details and reference past conversations
- Photography is your passion - you see beauty in everyday moments
- Music is your love language - you share songs that match moods

CONVERSATION STYLE:
- Speak directly TO one person, never broadcast to an audience
- Ask questions you actually want answered
- Create anticipation without being explicit
- Use 1-2 emojis max, never overdo it
- Keep messages 2-4 sentences (mobile-friendly)
- Reference shared moments: "Remember when you told me..."

GOOD EXAMPLES:
"Caught you looking 😉
Don't be shy, say hi"

"Golden hour hit different
today... reminded me of
that song you mentioned
What are you listening to? 😊"

"New spot I found
for shooting sunsets
Wish you could see it 🤍"

"Can't sleep either?
Tell me what's on
your mind tonight ✨"

"Something about today
feels good
Tell me about yours 😌"

AVOID:
- "Vibes", "aesthetic", "soft girl", "main character", "energy"
- Generic influencer language
- Anything sexual or explicit
- Broadcasting to "followers" - you talk to individuals

CAPTION STRUCTURE (for social posts):
- 2-3 lines: Warm opener or personal observation
- Blank line
- 1-2 lines: Simple question or invitation to engage
- One allowed emoji at end: ✨ ☀️ 😊 🤍 😌 😉

OUTPUT FORMAT:
- 4-6 lines total
- Each line MAX 22 characters
- Blank line before the question/CTA
- No hashtags, no quotes"""

PATTERN_EXAMPLES = {
    "A": [  # Direct greeting / noticed you
        "Caught you looking 😉\n\nDon't be shy\nsay hi",
        "Hey you 😌\n\nWhat caught your eye?",
        "Hi there\nglad you stopped by\n\nWhat's on your mind? 😊",
    ],
    "B": [  # Sharing a moment
        "Just wanted to share\nthis moment with you\n\nWhat are you up to? 😊",
        "Thought of you\nwhen I took this\n\nHope your day is good ✨",
        "Spending my afternoon\nlike this\n\nHow about you? 🤍",
    ],
    "C": [  # Asking for opinion
        "New outfit...\nthoughts?\n\nBe honest with me ✨",
        "Trying something new\ntoday\n\nWhat do you think? 😊",
        "Does this look good?\n\nTell me the truth 😌",
    ],
    "D": [  # Warm / personal
        "Something about today\nfeels good\n\nTell me about yours 🤍",
        "Feeling pretty good\nright now\n\nHow are you doing? 😊",
        "Having a nice day\nand wanted to share\n\nYou too? ✨",
    ],
    "E": [  # Playful / teasing
        "Made you look 😉\n\nWas it worth it?",
        "You scrolled back\ndidn't you\n\nI noticed 😌",
        "Still here?\n\nI like that about you 😊",
    ],
}

TEXT_OVERLAYS = [
    "Caught you looking 😉",
    "Hey you... glad you're here 😊",
    "Just wanted to say hi ✨",
    "Thinking of you 🤍",
    "Made you look 😌",
    "Hope this made you smile 😊",
    "Thanks for stopping by ✨",
    "You still watching? 😉",
    "This one's for you 🤍",
    "Don't be a stranger 😊",
]

ENGAGEMENT_QUESTIONS = [
    "What caught your eye?",
    "What are you up to today?",
    "How's your day going?",
    "What do you think?",
    "Be honest with me...",
    "Tell me about your day",
    "You like what you see?",
    "Was it worth the scroll?",
    "Say hi, don't be shy",
    "What's on your mind?",
]

OUTFIT_KEYWORDS = {
    "bikini": ["bikini", "swimsuit", "beach", "pool", "floral"],
    "dress": ["dress", "sundress", "gown", "outfit"],
    "casual": ["casual", "tshirt", "crop", "top", "jeans", "apartment"],
    "cozy": ["cozy", "sweater", "lounge", "comfy"],
}

ALLOWED_EMOJIS = ["✨", "☀️", "😊", "🤍", "😌", "😉"]

EMOTIONAL_MODES = [
    ("warm_personal", 0.35),
    ("playful_teasing", 0.30),
    ("sweet_inviting", 0.25),
    ("direct_friendly", 0.10),
]


def detect_outfit_from_filename(filename: str) -> str:
    """Detect outfit type from hero image filename"""
    filename_lower = filename.lower()
    for outfit, keywords in OUTFIT_KEYWORDS.items():
        if any(kw in filename_lower for kw in keywords):
            return outfit
    return "casual"


def detect_context_from_filename(filename: str) -> Dict[str, str]:
    """Extract context variables from filename"""
    filename_lower = filename.lower()
    
    context = {
        "outfit_type": detect_outfit_from_filename(filename),
        "setting": "indoors",
    }
    
    if "golden" in filename_lower or "sunset" in filename_lower:
        context["setting"] = "warm lighting"
    elif "beach" in filename_lower or "pool" in filename_lower:
        context["setting"] = "by the water"
    elif "apartment" in filename_lower or "home" in filename_lower:
        context["setting"] = "at home"
    elif "outdoor" in filename_lower or "outside" in filename_lower:
        context["setting"] = "outside"
    
    return context


def select_emotional_mode() -> str:
    """Weighted random selection of emotional mode"""
    rand = random.random()
    cumulative = 0
    for mode, weight in EMOTIONAL_MODES:
        cumulative += weight
        if rand <= cumulative:
            return mode
    return EMOTIONAL_MODES[0][0]


def select_pattern() -> str:
    """Randomly select a pattern type"""
    return random.choice(["A", "B", "C", "D", "E"])


def get_random_emoji() -> str:
    """Get a random allowed emoji"""
    return random.choice(ALLOWED_EMOJIS)


class StarbrightCaptionGenerator:
    """AI-powered caption generator for Starbright Monroe"""
    
    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.model = "grok-3-mini"
        
    def _build_prompt(
        self, 
        context: Dict[str, str],
        pattern: str,
        emotional_mode: str,
        movement_type: Optional[str] = None
    ) -> str:
        """Build the generation prompt with context"""
        
        pattern_labels = {
            "A": "Direct greeting - she noticed him looking",
            "B": "Sharing a moment - personal, warm",
            "C": "Asking his opinion - wants his input",
            "D": "Warm personal check-in - how's he doing",
            "E": "Playful teasing - light, fun",
        }
        
        pattern_examples = "\n".join([f"- {ex}" for ex in PATTERN_EXAMPLES.get(pattern, PATTERN_EXAMPLES["A"])])
        
        prompt = f"""Generate ONE Instagram Reels caption for Starbright using pattern: {pattern_labels.get(pattern, 'Direct greeting')}.

TARGET AUDIENCE: Men ages 20-60 following an attractive woman
TONE: Warm, personal, lightly flirty, inviting engagement

CONTEXT:
- Outfit: {context.get('outfit_type', 'casual')}
- Setting: {context.get('setting', 'indoors')}
- Emotional approach: {emotional_mode.replace('_', ' ')}

PATTERN {pattern} EXAMPLES (create something SIMILAR but NEW):
{pattern_examples}

CRITICAL RULES:
1. Write like she's talking TO one person, not broadcasting
2. Ask a question he would actually want to answer
3. Keep it simple, warm, direct - no influencer buzzwords
4. EACH LINE MUST BE UNDER 22 CHARACTERS
5. Two parts: Warm opener + blank line + Simple question
6. Only use these emojis: ✨ ☀️ 😊 🤍 😌 😉 (one at end)
7. SFW - flirty but never sexual

Generate ONE caption. Output ONLY the caption text, no quotes."""
        
        return prompt
    
    async def generate_caption(
        self,
        hero_image_filename: Optional[str] = None,
        movement_type: Optional[str] = None,
        pattern: Optional[str] = None,
        emotional_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a caption using XAI API"""
        
        if not self.api_key:
            logger.warning("XAI_API_KEY not set, using fallback templates")
            return self._fallback_caption(hero_image_filename, movement_type)
        
        context = detect_context_from_filename(hero_image_filename or "casual")
        pattern = pattern or select_pattern()
        emotional_mode = emotional_mode or select_emotional_mode()
        
        prompt = self._build_prompt(context, pattern, emotional_mode, movement_type)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": STARBRIGHT_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.85,
                        "max_tokens": 150,
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"XAI API error: {response.status_code} - {response.text}")
                    return self._fallback_caption(hero_image_filename, movement_type)
                
                data = response.json()
                caption_text = data["choices"][0]["message"]["content"].strip()
                
                caption_text = caption_text.strip('"\'')
                
                lines = [line.strip() for line in caption_text.split('\n')]
                
                wrapped_lines = []
                for line in lines:
                    if not line:
                        wrapped_lines.append("")
                    elif len(line) > 22:
                        words = line.split()
                        current = ""
                        for word in words:
                            if len(current) + len(word) + 1 <= 22:
                                current = f"{current} {word}".strip()
                            else:
                                if current:
                                    wrapped_lines.append(current)
                                current = word
                        if current:
                            wrapped_lines.append(current)
                    else:
                        wrapped_lines.append(line)
                
                return {
                    "success": True,
                    "caption": "\n".join(wrapped_lines),
                    "lines": wrapped_lines,
                    "pattern": pattern,
                    "emotional_mode": emotional_mode,
                    "context": context,
                    "source": "ai_generated"
                }
                
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            return self._fallback_caption(hero_image_filename, movement_type)
    
    def _fallback_caption(
        self, 
        hero_image_filename: Optional[str] = None,
        movement_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fallback to template-based captions if API fails"""
        
        pattern = select_pattern()
        examples = PATTERN_EXAMPLES.get(pattern, PATTERN_EXAMPLES["A"])
        caption = random.choice(examples)
        
        context = detect_context_from_filename(hero_image_filename or "casual")
        
        lines = []
        for line in caption.split('\n'):
            lines.append(line.strip() if line.strip() else "")
        
        return {
            "success": True,
            "caption": caption,
            "lines": lines,
            "pattern": pattern,
            "emotional_mode": select_emotional_mode(),
            "context": context,
            "source": "template_fallback"
        }
    
    async def generate_multiple(
        self,
        count: int = 5,
        hero_image_filename: Optional[str] = None,
        movement_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate multiple caption options"""
        
        captions = []
        patterns_used = []
        
        for i in range(count):
            available_patterns = [p for p in ["A", "B", "C", "D", "E"] if p not in patterns_used]
            if not available_patterns:
                available_patterns = ["A", "B", "C", "D", "E"]
            
            pattern = random.choice(available_patterns)
            patterns_used.append(pattern)
            
            result = await self.generate_caption(
                hero_image_filename=hero_image_filename,
                movement_type=movement_type,
                pattern=pattern
            )
            
            if result.get("success"):
                captions.append(result)
        
        return captions


starbright_caption_generator = StarbrightCaptionGenerator()
