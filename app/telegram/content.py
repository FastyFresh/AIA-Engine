"""
Telegram Content Module - Photo detection, selection, and delivery
"""
import os
import re
import random
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

CONTENT_BASE = "content/telegram"

PHOTO_REQUEST_PATTERNS = [
    r'\b(send|show|share|give|see|want|get)\b.*(photo|pic|picture|image|selfie)',
    r'\b(photo|pic|picture|image|selfie)\b.*(send|show|share|please)',
    r'can i (see|get|have)',
    r'show me',
    r'send me (a|some)',
]


def detect_photo_request(text: str) -> bool:
    """Detect if user is asking for a photo"""
    text_lower = text.lower()
    for pattern in PHOTO_REQUEST_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def infer_photo_context(filename: str) -> str:
    """Infer photo context from filename for AI awareness"""
    filename_lower = filename.lower()
    
    contexts = []
    if any(x in filename_lower for x in ['bed', 'lying', 'cozy', 'morning']):
        contexts.append("bedroom/cozy setting")
    elif any(x in filename_lower for x in ['outdoor', 'lake', 'beach', 'nature']):
        contexts.append("outdoor/nature setting")
    elif any(x in filename_lower for x in ['selfie', 'mirror']):
        contexts.append("selfie")
    else:
        contexts.append("casual indoor photo")
    
    if any(x in filename_lower for x in ['smile', 'happy', 'laugh']):
        contexts.append("smiling")
    if any(x in filename_lower for x in ['crop', 'shorts', 'lingerie']):
        contexts.append("casual/intimate outfit")
    
    return ", ".join(contexts) if contexts else "personal photo"


def get_random_photo(persona_id: str, tier: str) -> Tuple[Optional[str], str]:
    """Get a random photo from the appropriate tier folder with context"""
    persona_folder = "starbright" if "starbright" in persona_id else "luna"
    
    tier_folders = []
    if tier == "vip":
        tier_folders = ["vip", "companion", "teaser"]
    elif tier == "companion":
        tier_folders = ["companion", "teaser"]
    else:
        tier_folders = ["teaser"]
    
    for folder in tier_folders:
        path = f"{CONTENT_BASE}/{persona_folder}/{folder}"
        if os.path.exists(path):
            files = [f for f in os.listdir(path) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            if files:
                chosen = random.choice(files)
                context = infer_photo_context(chosen)
                return f"{path}/{chosen}", context
    
    return None, ""


def get_photo_for_tier(persona_id: str, tier: str, specific_folder: str = None) -> Optional[str]:
    """Get a photo from a specific folder or tier-appropriate folder"""
    persona_folder = "starbright" if "starbright" in persona_id else "luna"
    
    if specific_folder:
        path = f"{CONTENT_BASE}/{persona_folder}/{specific_folder}"
        if os.path.exists(path):
            files = [f for f in os.listdir(path) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            if files:
                return f"{path}/{random.choice(files)}"
    
    photo_path, _ = get_random_photo(persona_id, tier)
    return photo_path


class ContentManager:
    """Manages content delivery for a persona"""
    
    def __init__(self, persona_id: str):
        self.persona_id = persona_id
        self.persona_folder = "starbright" if "starbright" in persona_id else "luna"
    
    def get_teaser_photo(self) -> Optional[str]:
        """Get a random teaser photo"""
        return get_photo_for_tier(self.persona_id, "free", "teaser")
    
    def get_tier_photo(self, tier: str) -> Tuple[Optional[str], str]:
        """Get a random photo appropriate for the user's tier"""
        return get_random_photo(self.persona_id, tier)
    
    def get_welcome_pack_photos(self, tier: str, count: int = 3) -> list:
        """Get photos for a welcome pack based on tier"""
        photos = []
        folder = "companion" if tier == "companion" else "vip"
        path = f"{CONTENT_BASE}/{self.persona_folder}/{folder}"
        
        if os.path.exists(path):
            files = [f for f in os.listdir(path) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            if files:
                selected = random.sample(files, min(count, len(files)))
                photos = [f"{path}/{f}" for f in selected]
        
        return photos
    
    def get_photo_request_context(self, has_photo: bool, tier: str) -> str:
        """Get context for AI about photo request handling"""
        if has_photo:
            return "[You are about to send a photo. Briefly acknowledge sending it without describing details you can't see. Keep it natural and flirty.]"
        elif tier == "free":
            return "[User asked for a photo but they're on free tier. Tease them and suggest subscribing to see more of you.]"
        return ""
    
    def get_no_photo_upsell_text(self) -> str:
        """Get persona-specific upsell text when photo not available"""
        texts = {
            "starbright_monroe": "Use /subscribe to unlock my exclusive content 💕",
            "luna_vale": "Subscribe if you want to see more of me."
        }
        return texts.get(self.persona_id, "Subscribe to unlock exclusive content!")
