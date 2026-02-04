"""
Transform Image to Starbright using SEEDream 4.5

Uses fal.ai Seedream 4.5 edit endpoint with multi-reference conditioning to transform
a source image into Starbright Monroe while preserving the exact pose and camera angle.
"""

import os
import base64
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

FAL_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

SOURCE_IMAGE = "attached_assets/SnapInsta.to_621833016_17877935706467396_2868144746515660684_n_1770180720096.jpg"
FACE_REF = "content/references/starbright_monroe/starbright_face_reference_v3.webp"
BODY_REF = "content/references/starbright_monroe/body_reference_canonical.webp"
OUTPUT_DIR = "content/seedream4_output"

STARBRIGHT_IDENTITY = (
    "very pale porcelain ivory white skin, "
    "straight sleek dark brown hair (not wavy, not curly), "
    "warm olive-brown eyes, natural freckles across nose and cheeks, "
    "extremely thin slender petite body with very narrow tiny waist, "
    "slim narrow hips, long thin slender legs, delicate small frame"
)

CAMERA_SETTINGS = "Shot on Canon EOS R5, 85mm f/1.4 lens, shallow depth of field"

SKIN_TEXTURE = (
    "natural skin texture with visible pores, subtle imperfections and tonal variations, "
    "faint natural sheen, slight skin asymmetry, realistic skin tones"
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


async def transform_image():
    """Transform the source image into Starbright with modern luxury background"""
    
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not configured")
        return None
    
    if not Path(SOURCE_IMAGE).exists():
        print(f"ERROR: Source image not found: {SOURCE_IMAGE}")
        return None
    if not Path(FACE_REF).exists():
        print(f"ERROR: Face reference not found: {FACE_REF}")
        return None
    if not Path(BODY_REF).exists():
        print(f"ERROR: Body reference not found: {BODY_REF}")
        return None
    
    print("Encoding reference images...")
    source_b64 = encode_image(SOURCE_IMAGE)
    face_b64 = encode_image(FACE_REF)
    body_b64 = encode_image(BODY_REF)
    
    prompt = f"""Transform this image: Figure 3 shows the exact pose and camera angle to recreate.
Figure 1 is the face reference - use this exact face identity.
Figure 2 is the body reference - use this exact body type and proportions.

Create a hyper-realistic photo of {STARBRIGHT_IDENTITY}.

She is in a modern luxury penthouse apartment with floor-to-ceiling windows, 
bright natural daylight flooding the room, minimalist contemporary furniture, 
neutral tones with white marble accents, elegant sophisticated interior design.

Maintain the EXACT same pose, camera angle, and body positioning as Figure 3.
Dress her in a stylish fitted black mini dress with thin straps, black thigh-high stockings.

{CAMERA_SETTINGS}. {SKIN_TEXTURE}. 
Professional fashion photography, bright natural lighting, high-key exposure, 
8K ultra detailed, photorealistic."""

    negative_prompt = (
        "extra limbs, extra legs, extra arms, extra fingers, missing limbs, "
        "deformed body, disproportionate body, unnatural anatomy, distorted proportions, "
        "mutated hands, fused fingers, too many fingers, missing fingers, "
        "bad anatomy, wrong anatomy, unrealistic body, mannequin, plastic skin, "
        "dark lighting, dim, shadows, low key, underexposed"
    )
    
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "image_urls": [face_b64, body_b64, source_b64],
        "image_size": "auto_4K",
        "num_images": 1,
        "max_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": negative_prompt
    }
    
    print("Sending request to fal.ai Seedream 4.5 edit endpoint...")
    print(f"Using 3 reference images: face, body, source pose")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                FAL_EDIT_URL,
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
                            filename = f"starbright_transform_{timestamp}.png"
                            filepath = Path(OUTPUT_DIR) / filename
                            filepath.write_bytes(img_resp.content)
                            
                            print(f"SUCCESS! Image saved: {filepath}")
                            print(f"Seed used: {result.get('seed')}")
                            return str(filepath)
                
                print("ERROR: No images in response")
                print(result)
                return None
            
            elif response.status_code == 422:
                error = response.json()
                print(f"Content validation error: {error}")
                return None
            
            else:
                print(f"API error {response.status_code}: {response.text[:500]}")
                return None
                
    except httpx.TimeoutException:
        print("ERROR: Request timeout (>300s)")
        return None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None


if __name__ == "__main__":
    result = asyncio.run(transform_image())
    if result:
        print(f"\nTransformation complete! Output: {result}")
    else:
        print("\nTransformation failed.")
