from typing import Any, Dict
from app.agents.base import BaseAgent
from app.config import InfluencerConfig

class IdentityAgent(BaseAgent):
    def __init__(self):
        super().__init__("IdentityAgent")
    
    async def run(self, influencer: InfluencerConfig) -> Dict[str, Any]:
        self.log(f"Loading identity for {influencer.name}")
        
        identity_context = {
            "name": influencer.name,
            "handle": influencer.handle,
            "niche": influencer.niche,
            "aesthetic": influencer.aesthetic,
            "voice_tone": self._generate_voice_tone(influencer),
            "content_themes": self._generate_themes(influencer)
        }
        
        self.log(f"Identity context loaded for {influencer.name}")
        return identity_context
    
    def _generate_voice_tone(self, influencer: InfluencerConfig) -> str:
        tones = {
            "Lifestyle & Wellness": "Warm, encouraging, and authentic",
            "Fashion & Beauty": "Bold, confident, and trendsetting"
        }
        return tones.get(influencer.niche, "Friendly and engaging")
    
    def _generate_themes(self, influencer: InfluencerConfig) -> list:
        themes = {
            "Lifestyle & Wellness": ["self-care", "mindfulness", "healthy living", "motivation"],
            "Fashion & Beauty": ["style tips", "makeup tutorials", "fashion trends", "glam looks"]
        }
        return themes.get(influencer.niche, ["lifestyle", "content"])
