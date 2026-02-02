"""
Background Analyzer using Grok Vision
Analyzes source images and maps backgrounds to our preset library.
Uses xAI Grok vision (blueprint:python_xai)
"""
import os
import base64
import json
from pathlib import Path
from openai import OpenAI

# Background presets from our library
BACKGROUND_PRESETS = {
    "apartment_bedroom_day": {
        "description": "spacious bright modern luxury penthouse bedroom, floor-to-ceiling windows with natural morning sunlight, high double-height ceilings, designer furniture, king size bed with rumpled white sheets, personal items scattered",
        "keywords": ["bedroom", "bed", "morning", "daylight", "bright"]
    },
    "apartment_bedroom_night": {
        "description": "modern luxury penthouse bedroom, warm evening ambient lighting, floor-to-ceiling windows showing city lights at night, cozy atmosphere, king size bed with rumpled sheets",
        "keywords": ["bedroom", "bed", "night", "evening", "dark", "ambient"]
    },
    "apartment_living_day": {
        "description": "spacious modern luxury penthouse living room, bright natural daylight through floor-to-ceiling windows, designer sofa and furniture, high ceilings, minimalist decor",
        "keywords": ["living room", "sofa", "couch", "lounge", "daylight"]
    },
    "apartment_living_night": {
        "description": "modern luxury penthouse living room, warm evening lighting, floor-to-ceiling windows with city skyline at night, designer furniture",
        "keywords": ["living room", "sofa", "night", "evening"]
    },
    "bathroom_luxury": {
        "description": "spacious luxury marble bathroom, modern fixtures, large mirror, bright lighting, spa-like atmosphere",
        "keywords": ["bathroom", "mirror", "sink", "shower", "bath"]
    },
    "gym_modern": {
        "description": "modern high-end private gym, exercise equipment, mirrored walls, bright lighting",
        "keywords": ["gym", "fitness", "workout", "exercise", "equipment"]
    },
    "studio_white": {
        "description": "professional photography studio with pure white seamless background, soft diffused lighting",
        "keywords": ["studio", "white background", "plain", "simple", "professional"]
    },
    "outdoor_pool": {
        "description": "luxury infinity pool overlooking ocean or city, sunset golden hour lighting, palm trees",
        "keywords": ["pool", "outdoor", "sunset", "beach", "water"]
    }
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
        
        preset_list = "\n".join([f"- {k}: {v['description']}" for k, v in BACKGROUND_PRESETS.items()])
        
        response = self.client.chat.completions.create(
            model="grok-2-vision-1212",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Analyze the background/setting of this image. 

First, describe what you see in the background (room type, lighting, time of day, key elements).

Then, choose the BEST matching preset from this list:
{preset_list}

Respond with JSON:
{{"background_description": "brief description of what you see", "time_of_day": "day or night", "matched_preset": "preset_name", "confidence": 0.0-1.0}}"""
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
        
        # Get the full description for the matched preset
        preset_info = BACKGROUND_PRESETS.get(matched, BACKGROUND_PRESETS["apartment_bedroom_day"])
        result["preset_description"] = preset_info["description"]
        
        return result


if __name__ == "__main__":
    # Test with one image
    analyzer = BackgroundAnalyzer()
    test_img = "content/transform_input/012426transform 4/SnapInsta.to_398602122_325603090216830_2559318016282510058_n.jpg"
    result = analyzer.analyze_background(test_img)
    print(json.dumps(result, indent=2))
