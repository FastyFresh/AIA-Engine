"""
Transform Image using ControlNet for EXACT Pose Matching

Uses fal.ai Z-Image Turbo with ControlNet pose detection to extract and enforce
the exact pose skeleton from the source image.
"""

import os
import base64
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

FAL_CONTROLNET_URL = "https://fal.run/fal-ai/z-image/turbo/controlnet"

SOURCE_IMAGE = "attached_assets/SnapInsta.to_621833016_17877935706467396_2868144746515660684_n_1770180720096.jpg"
OUTPUT_DIR = "content/seedream4_output"

STARBRIGHT_IDENTITY = (
    "young woman with very pale porcelain ivory white skin, "
    "straight sleek dark brown hair parted in middle (not wavy, not curly, not black), "
    "warm olive-brown eyes (not blue, not grey), natural freckles across nose and cheeks, "
    "extremely thin slender petite body with very narrow tiny waist, "
    "slim narrow hips, long thin slender legs, delicate small frame, "
    "small natural breasts, proportionate feminine figure"
)

def encode_image(path: str) -> str:
    """Encode image to base64 data URI"""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    
    ext = Path(path).suffix.lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }.get(ext, "image/png")
    
    return f"data:{mime};base64,{data}"


async def transform_with_controlnet():
    """Transform using ControlNet pose extraction for exact pose matching"""
    
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not configured")
        return None
    
    print("Encoding source image for pose extraction...")
    source_b64 = encode_image(SOURCE_IMAGE)
    
    prompt = f"""{STARBRIGHT_IDENTITY}, 
wearing a stylish fitted black mini dress with thin straps, black thigh-high stockings,
in a modern luxury penthouse apartment with floor-to-ceiling windows, 
bright natural daylight flooding the room, white marble floors, 
contemporary minimalist furniture, elegant sophisticated interior design,
Shot on Canon EOS R5, 85mm f/1.4 lens, shallow depth of field,
natural skin texture with visible pores, subtle imperfections,
professional fashion photography, bright natural lighting, high-key exposure,
8K ultra detailed, photorealistic, candid professional feel"""

    negative_prompt = (
        "blue eyes, grey eyes, black hair, wavy hair, curly hair, "
        "extra limbs, deformed body, unnatural anatomy, "
        "mutated hands, bad anatomy, plastic skin, airbrushed, "
        "dark lighting, dim, shadows, underexposed, "
        "cartoon, anime, illustration, 3D render"
    )
    
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "image_url": source_b64,
        "preprocess": "pose",
        "control_strength": 0.95,
        "num_images": 1,
        "image_size": {"width": 1024, "height": 1280},
        "guidance_scale": 7.5,
        "num_inference_steps": 30,
        "negative_prompt": negative_prompt,
        "enable_safety_checker": False
    }
    
    print("Sending request to Z-Image Turbo with ControlNet POSE...")
    print("Control strength: 0.95 (high adherence to exact pose)")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                FAL_CONTROLNET_URL,
                headers=headers,
                json=payload
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                images = result.get("images", [])
                
                if images:
                    img_url = images[0].get("url", "")
                    if img_url:
                        print(f"Downloading generated image...")
                        img_resp = await client.get(img_url)
                        if img_resp.status_code == 200:
                            Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"starbright_controlnet_pose_{timestamp}.png"
                            filepath = Path(OUTPUT_DIR) / filename
                            filepath.write_bytes(img_resp.content)
                            
                            print(f"SUCCESS! Image saved: {filepath}")
                            print(f"Seed: {result.get('seed')}")
                            return str(filepath)
                
                print("ERROR: No images in response")
                print(result)
                return None
            
            else:
                print(f"API error {response.status_code}: {response.text[:500]}")
                return None
                
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None


if __name__ == "__main__":
    result = asyncio.run(transform_with_controlnet())
    if result:
        print(f"\nControlNet pose transformation complete! Output: {result}")
    else:
        print("\nTransformation failed.")
