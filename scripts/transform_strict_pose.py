"""
Transform Image to Starbright with STRICT Pose Matching

Uses fal.ai Seedream 4.5 edit with source image as Figure 1 (highest weight)
to maximize pose adherence.
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


async def transform_strict_pose():
    """Transform with source image as Figure 1 for strict pose matching"""
    
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not configured")
        return None
    
    print("Encoding reference images...")
    source_b64 = encode_image(SOURCE_IMAGE)
    face_b64 = encode_image(FACE_REF)
    body_b64 = encode_image(BODY_REF)
    
    prompt = f"""CRITICAL: Keep the EXACT pose, body position, camera angle, and composition from Figure 1 completely unchanged. Do not alter the pose in any way.

Figure 1 is the POSE REFERENCE - copy this exact pose precisely: the leaning forward position, hand placement on floor, leg positioning, head tilt, and camera angle from above.

Figure 2 is the FACE REFERENCE - apply this exact face identity to the person.
Figure 3 is the BODY REFERENCE - use these body proportions: {STARBRIGHT_IDENTITY}.

Transform the person in Figure 1 to have:
- The exact face from Figure 2 (pale porcelain skin, straight dark brown hair, olive-brown eyes, freckles)
- The slender petite body proportions from Figure 3
- Keep the same black fitted mini dress with thin straps
- Keep the same black thigh-high stockings

Change ONLY the background to: modern luxury penthouse apartment with floor-to-ceiling windows, bright natural daylight flooding in, white marble floors, contemporary minimalist furniture.

The pose, camera angle, and body positioning must match Figure 1 EXACTLY.

Shot on Canon EOS R5, 85mm f/1.4 lens. Natural skin texture with visible pores. 
Professional fashion photography, bright natural lighting, 8K ultra detailed."""

    negative_prompt = (
        "different pose, altered pose, changed position, modified angle, "
        "extra limbs, deformed body, unnatural anatomy, "
        "mutated hands, bad anatomy, plastic skin, "
        "dark lighting, dim, shadows, underexposed"
    )
    
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "image_urls": [source_b64, face_b64, body_b64],
        "image_size": "auto_4K",
        "num_images": 1,
        "max_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": negative_prompt
    }
    
    print("Sending request with SOURCE IMAGE as Figure 1 (highest priority)...")
    print("Order: Figure 1=source pose, Figure 2=face, Figure 3=body")
    
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
                            filename = f"starbright_strict_pose_{timestamp}.png"
                            filepath = Path(OUTPUT_DIR) / filename
                            filepath.write_bytes(img_resp.content)
                            
                            print(f"SUCCESS! Image saved: {filepath}")
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
    result = asyncio.run(transform_strict_pose())
    if result:
        print(f"\nStrict pose transformation complete! Output: {result}")
    else:
        print("\nTransformation failed.")
