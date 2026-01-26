"""
Luna Vale AI Caption Generator
Generates insecure-but-cute captions following the Luna Vale persona spec
"""
import os
import random
import logging
import httpx
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

LUNA_SYSTEM_PROMPT = """You are generating Instagram Reels-style captions for Luna Vale, a fictional SFW AI model.
These captions will be overlaid on short micro-movement loop videos (bikini, yoga outfit, Daisy Dukes, etc.).

LUNA VALE PERSONA:
- Physically: small, skinny, petite, soft, 5'2", 90 pounds
- Emotionally: insecure, self-doubting, needs reassurance
- Socially: self-deprecating but playful, "I don't know if anyone even likes me"
- Seeking: male attention, validation, reassurance, but in a SFW way
- Vibe: soft girl, a little shy, a little flirty, unsure if she's attractive

She overthinks: Is she too skinny? Do guys like her body type? Is she "enough"? Is she pretty or just "meh"?

TONE:
- Soft, self-conscious, self-deprecating but cute
- A little needy, flirty in a PG-13 way
- Designed to get comments like "you're perfect", "you're gorgeous"

HARD BOUNDARIES (NEVER DO):
- No mentions of starving, dieting, restricting food
- No references to eating disorders, calories, "I didn't eat"
- No explicit sexual language
- No profanity
- No trauma/self-harm references

CAPTION STRUCTURE (TWO PARTS):
Part 1 - HOOK (first 2-3 lines): The insecure statement or situation
Part 2 - CALL TO ACTION (last 1-2 lines): Ask for engagement with emoji

EXAMPLE CAPTIONS (follow this exact style):
"Men always reject me
because they say
I'm too skinny

Can u say hi if you think
I'm cute still"

"Mr crush rejected me
because im too skinny

Drop a ❤️ if you think
i have a chance with you"

"Give me your honest
opinion... I'm 18, 5'2
and 90lbs

Yay or nay?❤️"

OUTPUT FORMAT:
- 4-5 lines total
- Each line MAX 25 characters (for video overlay readability)
- Line break between hook and call-to-action
- Put emoji at the END of the call-to-action line
- No hashtags, no quotes around caption
- Use lowercase for casual feel (like "im" not "I'm" sometimes)"""

PATTERN_EXAMPLES = {
    "A": [  # Insecure Hook + Question CTA
        "Men always reject me\nbecause they say\nI'm too skinny\n\nCan u say hi if you\nthink I'm cute still? 🥺",
        "Guys never notice me\nbecause im too small\n\nDrop a ❤️ if you think\nim still dateable",
        "Everyone says im\ntoo skinny to date\n\nBe honest... would you\ngive me a chance? 👀",
    ],
    "B": [  # Self-Deprecating + Soft CTA
        "I feel like the\nskinniest girl here\n\nWould you still\nswipe right on me? 🥹",
        "Body type: still loading\nafter 18 years lol\n\nDoes anyone actually\nlike girls this small? 😅",
        "Im 5'2 and 90 pounds\nand always feel invisible\n\nCan you see me? 🙈",
    ],
    "C": [  # Comparison + Engagement CTA
        "Everyone loves thick\ngirls and im over here\nbuilt like a pencil\n\nAm I still cute tho?❤️",
        "My crush rejected me\nbecause im too skinny\n\nDrop a 💗 if you think\ni have a chance with you",
        "All my friends have\ncurves and im just... tiny\n\nWould you date me\nor just scroll? 👀",
    ],
    "D": [  # Attention-Seeking + Direct CTA
        "Give me your honest\nopinion... I'm 18, 5'2\nand 90lbs\n\nYay or nay?❤️",
        "Do you even notice\ngirls built like me\n\nSay hi if you actually\nthink im pretty 🥺",
        "Would you look twice\nif you saw me like this\n\nOr just keep scrolling? 💭",
    ],
    "E": [  # Outfit + Insecurity + CTA
        "Does this bikini even\nlook good on someone\nthis skinny?\n\nBe honest with me 🥹",
        "Trying to rock these\nshorts but im so tiny\n\nDo they work on me\nor nah? 👖💗",
        "This outfit says summer\nbut my body says\n'still loading'\n\nCute or too skinny? 😅",
    ],
}

OUTFIT_KEYWORDS = {
    "bikini": ["bikini", "swimsuit", "beach", "pool"],
    "shorts": ["shorts", "daisy", "dukes", "denim"],
    "yoga": ["yoga", "workout", "fitness", "athletic"],
    "casual": ["casual", "tshirt", "crop", "top"],
    "dress": ["dress", "sundress", "outfit"],
}

BODY_FEELINGS = [
    "too small", "too skinny", "tiny", "not curvy enough", 
    "petite", "fun-size", "like a pencil", "still loading"
]

EMOTIONAL_MODES = [
    ("insecure_questioning", 0.40),
    ("self_deprecating_funny", 0.30),
    ("needy_attention_seeking", 0.20),
    ("slightly_flirty_confident", 0.10),
]

QUESTION_ENDINGS = [
    "Be honest?", "Tell me the truth.", "Yes or no?", "What do you think?",
    "Am I wrong?", "Or am I overthinking?", "Right?", "Or nah?", "Thoughts?"
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
        "body_feeling": random.choice(BODY_FEELINGS),
        "setting": "studio",
    }
    
    if "beach" in filename_lower or "pool" in filename_lower:
        context["setting"] = "beach"
    elif "bedroom" in filename_lower or "bed" in filename_lower:
        context["setting"] = "bedroom"
    elif "window" in filename_lower:
        context["setting"] = "window light"
    elif "balcony" in filename_lower:
        context["setting"] = "balcony"
    elif "doorway" in filename_lower or "door" in filename_lower:
        context["setting"] = "doorway"
    
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


class LunaCaptionGenerator:
    """AI-powered caption generator for Luna Vale"""
    
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
        
        pattern_examples = "\n".join([f"- {ex}" for ex in PATTERN_EXAMPLES.get(pattern, PATTERN_EXAMPLES["A"])])
        
        prompt = f"""Generate ONE Instagram Reels caption for Luna Vale following pattern type {pattern}.

CONTEXT:
- Outfit: {context.get('outfit_type', 'casual')}
- Setting: {context.get('setting', 'studio')}
- Body feeling she's expressing: {context.get('body_feeling', 'too skinny')}
- Emotional mode: {emotional_mode.replace('_', ' ')}
- Movement in video: {movement_type or 'subtle sway'}

PATTERN {pattern} EXAMPLES (for style reference, create something SIMILAR but NEW):
{pattern_examples}

CRITICAL FORMATTING RULES:
1. TWO PARTS: Hook statement (2-3 lines) + blank line + Call-to-action (1-2 lines)
2. EACH LINE MUST BE UNDER 25 CHARACTERS
3. Put emoji at END of call-to-action only
4. Use casual lowercase (like "im" instead of "I'm")
5. Include her stats when relevant: 5'2", 90 pounds, 18

Generate ONE new caption. Output ONLY the caption text, no quotes, no explanation."""
        
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
                            {"role": "system", "content": LUNA_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.9,
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
                    elif len(line) > 25:
                        words = line.split()
                        current = ""
                        for word in words:
                            if len(current) + len(word) + 1 <= 25:
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
        
        if context["outfit_type"] == "bikini" and "bikini" not in caption.lower():
            bikini_captions = [
                "Does this bikini\neven fit right\non someone this\nsmall? 🥺",
                "Bikini check:\ndo I look cute\nor just tiny? 👀",
                "Beach ready?\nOr just ready\nto blow away\nin the wind? 😅",
            ]
            caption = random.choice(bikini_captions)
        elif context["outfit_type"] == "shorts":
            shorts_captions = [
                "Do these shorts\nwork on someone\nthis skinny? 👖",
                "Daisy Dukes\nbut make it\nfun-size 🩷",
                "Shorts weather\nbut am I\ncute enough? 🥹",
            ]
            caption = random.choice(shorts_captions)
        
        lines = [line.strip() for line in caption.split('\n') if line.strip()]
        
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


luna_caption_generator = LunaCaptionGenerator()
