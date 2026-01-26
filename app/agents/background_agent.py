"""
Background Agent - Manages scene/background references for consistent content generation
Maps content themes to appropriate background images from the library
"""
import os
import random
from pathlib import Path
from typing import Optional, Dict, List

BACKGROUNDS_DIR = Path("content/backgrounds")

BACKGROUND_LIBRARY = {
    "apartment_living_day": {
        "file": "apartment_day.png",
        "description": "Modern luxury apartment living room, bright daylight",
        "themes": ["selfie_saturday", "casual"],
        "time": "day"
    },
    "apartment_living_night": {
        "file": "apartment_night.png",
        "description": "Modern luxury apartment living room, warm evening",
        "themes": ["tease_tuesday", "fanvue_friday", "evening"],
        "time": "night"
    },
    "apartment_bedroom_day": {
        "file": "apartment_bedroom_day.png",
        "description": "Luxury bedroom with morning light",
        "themes": ["motivation_monday", "wellness_wednesday", "morning"],
        "time": "day"
    },
    "apartment_bedroom_night": {
        "file": "apartment_bedroom_night.png",
        "description": "Luxury bedroom with warm evening lighting",
        "themes": ["tease_tuesday", "soft_sunday", "fanvue_friday", "intimate"],
        "time": "night"
    },
    "gym_modern": {
        "file": "gym_modern.png",
        "description": "Modern luxury gym interior",
        "themes": ["motivation_monday", "wellness_wednesday", "fitness"],
        "time": "day"
    },
    "infinity_pool_sunset": {
        "file": "infinity_pool_sunset.png",
        "description": "Luxury infinity pool at sunset",
        "themes": ["thirsty_thursday", "vacation", "summer"],
        "time": "golden_hour"
    },
    "spa_wellness": {
        "file": "spa_wellness.png",
        "description": "Luxury spa wellness center",
        "themes": ["wellness_wednesday", "self_care", "relaxation"],
        "time": "day"
    },
    "beach_sunset": {
        "file": "beach_sunset.png",
        "description": "Tropical beach at golden hour",
        "themes": ["thirsty_thursday", "vacation", "summer"],
        "time": "golden_hour"
    },
    "bathroom_luxury": {
        "file": "bathroom_luxury.png",
        "description": "Luxury marble bathroom",
        "themes": ["soft_sunday", "self_care", "intimate"],
        "time": "day"
    },
}

THEME_TO_BACKGROUND = {
    "motivation_monday": ["gym_modern", "apartment_bedroom_day"],
    "tease_tuesday": ["apartment_bedroom_night", "apartment_living_night"],
    "wellness_wednesday": ["spa_wellness", "gym_modern", "apartment_bedroom_day"],
    "thirsty_thursday": ["infinity_pool_sunset", "beach_sunset"],
    "fanvue_friday": ["apartment_bedroom_night", "apartment_living_night"],
    "selfie_saturday": ["apartment_living_day", "apartment_bedroom_day", "bathroom_luxury"],
    "soft_sunday": ["apartment_bedroom_night", "apartment_living_night", "bathroom_luxury"],
}


class BackgroundAgent:
    def __init__(self):
        self.backgrounds_dir = BACKGROUNDS_DIR
        self.used_today = []
    
    def reset_daily_usage(self):
        self.used_today = []
    
    def get_background_for_theme(
        self,
        theme: str,
        time_of_day: Optional[str] = None,
        avoid_recent: bool = True
    ) -> Optional[Dict]:
        """Get appropriate background for a content theme"""
        theme_key = theme.lower().replace(" ", "_")
        
        available = THEME_TO_BACKGROUND.get(theme_key, list(BACKGROUND_LIBRARY.keys()))
        
        if time_of_day:
            available = [
                bg for bg in available 
                if BACKGROUND_LIBRARY.get(bg, {}).get("time") == time_of_day
            ]
        
        if avoid_recent and self.used_today:
            filtered = [bg for bg in available if bg not in self.used_today[-3:]]
            if filtered:
                available = filtered
        
        if not available:
            return None
        
        selected = random.choice(available)
        self.used_today.append(selected)
        
        bg_info = BACKGROUND_LIBRARY.get(selected, {})
        bg_path = self.backgrounds_dir / bg_info.get("file", "")
        
        if not bg_path.exists():
            return None
        
        return {
            "id": selected,
            "path": str(bg_path),
            "description": bg_info.get("description", ""),
            "time": bg_info.get("time", ""),
        }
    
    def get_background_path(self, background_id: str) -> Optional[str]:
        """Get the file path for a specific background"""
        bg_info = BACKGROUND_LIBRARY.get(background_id)
        if not bg_info:
            return None
        
        path = self.backgrounds_dir / bg_info.get("file", "")
        return str(path) if path.exists() else None
    
    def list_backgrounds(self) -> List[Dict]:
        """List all available backgrounds"""
        result = []
        for bg_id, info in BACKGROUND_LIBRARY.items():
            path = self.backgrounds_dir / info.get("file", "")
            result.append({
                "id": bg_id,
                "file": info.get("file"),
                "description": info.get("description"),
                "themes": info.get("themes"),
                "time": info.get("time"),
                "exists": path.exists()
            })
        return result
    
    def get_prompt_snippet(self, background_id: str) -> str:
        """Get a prompt-friendly description of the background"""
        bg_info = BACKGROUND_LIBRARY.get(background_id)
        if not bg_info:
            return ""
        return bg_info.get("description", "")


background_agent = BackgroundAgent()
