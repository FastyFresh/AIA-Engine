"""
Background Analyzer using Grok Vision
Analyzes source images and maps backgrounds to our preset library.
Uses xAI Grok vision (blueprint:python_xai)

See docs/starbright_transformation_guide.md for full documentation.
"""
import os
import base64
import json
from pathlib import Path
from openai import OpenAI

# Background presets - PURE room types only (no combined spaces)
BACKGROUND_PRESETS = {
    "apartment_bedroom_day": {
        "description": "Luxury bedroom interior only, king size bed with rumpled white sheets as focal point, elegant nightstands with lamps, soft morning sunlight through sheer curtains, warm wood floors, personal items on dresser, NO living room furniture, NO sofa, NO dining area, NO open floor plan",
        "keywords": ["bedroom", "bed", "morning", "daylight", "bright", "intimate", "lingerie", "bra", "underwear"]
    },
    "apartment_bedroom_night": {
        "description": "Luxury bedroom interior only, king size bed with rumpled sheets, warm ambient bedside lighting, city lights visible through window, intimate cozy atmosphere, nightstands with soft lamps, NO living room, NO sofa, NO open concept space",
        "keywords": ["bedroom", "bed", "night", "evening", "dark", "ambient", "intimate"]
    },
    "apartment_living_day": {
        "description": "Modern luxury penthouse living room, black leather tufted sofa and armchairs, glass coffee table with books, floor-to-ceiling windows with city skyline view, bright natural daylight, modern abstract art on walls, hardwood floors, NO bed, NO bedroom visible",
        "keywords": ["living room", "sofa", "couch", "lounge", "daylight", "casual", "clothed"]
    },
    "apartment_living_night": {
        "description": "Modern luxury penthouse living room, black leather tufted sofa, warm evening ambient lighting, floor-to-ceiling windows showing city skyline at night, modern fireplace, hardwood floors, NO bed, NO bedroom visible",
        "keywords": ["living room", "sofa", "night", "evening", "social"]
    },
    "bathroom_luxury": {
        "description": "Spacious luxury marble bathroom, large frameless mirror, modern vessel sink, rainfall shower visible, spa-like atmosphere with plants, bright even lighting, fluffy white towels",
        "keywords": ["bathroom", "mirror", "sink", "shower", "bath", "towel", "spa"]
    },
    "gym_modern": {
        "description": "Modern high-end private home gym, exercise equipment like dumbbells and yoga mat, large mirrors on wall, bright motivational lighting, rubber flooring",
        "keywords": ["gym", "fitness", "workout", "exercise", "equipment", "athletic", "sports"]
    },
    "studio_white": {
        "description": "Professional photography studio with pure white seamless paper backdrop, visible lighting equipment and stands, soft diffused studio lighting, clean minimal setup",
        "keywords": ["studio", "white background", "plain", "simple", "professional", "photoshoot", "clean"]
    },
    "outdoor_pool": {
        "description": "Luxury infinity pool overlooking ocean or cityscape, golden hour sunset lighting, palm trees and tropical plants, poolside loungers with towels",
        "keywords": ["pool", "outdoor", "sunset", "beach", "water", "swim", "bikini", "tropical"]
    }
}

# Outfit to background mapping - intimate wear goes to bedroom only
OUTFIT_BACKGROUND_RULES = {
    "lingerie": "apartment_bedroom",
    "bra": "apartment_bedroom",
    "underwear": "apartment_bedroom",
    "panties": "apartment_bedroom",
    "negligee": "apartment_bedroom",
    "bikini": "outdoor_pool",
    "swimsuit": "outdoor_pool",
    "workout": "gym_modern",
    "athletic": "gym_modern",
    "sports": "gym_modern"
}


class BackgroundAnalyzer:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=os.environ.get("XAI_API_KEY", "")
        )
    
    def encode_image(self, path: str) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def analyze_background(self, image_path: str) -> dict:
        """Analyze image background and map to our presets"""
        base64_image = self.encode_image(image_path)
        ext = Path(image_path).suffix.lower()
        mime = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".webp": "webp"}.get(ext, "jpeg")
        
        preset_list = "\n".join([f"- {k}: {v['description'][:100]}..." for k, v in BACKGROUND_PRESETS.items()])
        
        response = self.client.chat.completions.create(
            model="grok-2-vision-1212",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Analyze this image and provide:

1. Background/setting description (room type, lighting, time of day)
2. What the person is wearing (outfit type)
3. Best matching preset from this list:
{preset_list}

IMPORTANT RULES:
- If wearing lingerie/underwear/bra → MUST use apartment_bedroom_day or apartment_bedroom_night
- If wearing bikini/swimwear → MUST use outdoor_pool
- If wearing workout clothes → MUST use gym_modern
- If on white/plain background → use studio_white
- Otherwise match based on the background in the image

Respond with JSON:
{{"background_description": "what you see", "outfit_type": "clothing description", "time_of_day": "day or night", "matched_preset": "preset_name", "confidence": 0.0-1.0}}"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/{mime};base64,{base64_image}"}
                    }
                ]
            }],
            response_format={"type": "json_object"},
            max_tokens=500
        )
        
        result = json.loads(response.choices[0].message.content)
        matched = result.get("matched_preset", "apartment_bedroom_day")
        
        # Override based on outfit if detected
        outfit = result.get("outfit_type", "").lower()
        for keyword, bg_prefix in OUTFIT_BACKGROUND_RULES.items():
            if keyword in outfit:
                time = result.get("time_of_day", "day")
                if bg_prefix in ["apartment_bedroom", "apartment_living"]:
                    matched = f"{bg_prefix}_{time}"
                else:
                    matched = bg_prefix
                result["outfit_override"] = True
                break
        
        # Ensure matched preset exists
        if matched not in BACKGROUND_PRESETS:
            matched = "apartment_bedroom_day"
        
        result["matched_preset"] = matched
        result["preset_description"] = BACKGROUND_PRESETS[matched]["description"]
        
        return result


if __name__ == "__main__":
    # Test with one image
    analyzer = BackgroundAnalyzer()
    test_img = "content/transform_input/012426transform 4/SnapInsta.to_398602122_325603090216830_2559318016282510058_n.jpg"
    result = analyzer.analyze_background(test_img)
    print(json.dumps(result, indent=2))
