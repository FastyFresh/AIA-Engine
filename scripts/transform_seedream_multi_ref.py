"""
SEEDream 4.5 Multi-Reference Transformation

Optimal prompting strategy for 4 references:
- Image 1: Pose/outfit reference (what to transform)
- Image 2: Face reference (Starbright's face with skin texture)
- Image 3: Body reference (Starbright's body proportions)
- Image 4: Background reference (target environment)

Uses explicit reference assignment pattern for SEEDream 4.5
"""

import os
import base64
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

FAL_SEEDREAM_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

POSE_REF = "attached_assets/pose_ref_1_1770181950291.webp"
FACE_REF = "attached_assets/starbright_face_reference_v2_1770181950291.webp"
BODY_REF = "attached_assets/body_reference_goal_1770181950292.webp"
BG_REF = "attached_assets/reference,_living_room,_background_1770181950292.png"

OUTPUT_DIR = "content/seedream4_output"

MULTI_REF_PROMPT = """Using Image 1 for pose, outfit, hairstyle and camera angle.
Using Image 2 for background environment, room layout, and lighting.
Using Image 3 for facial features, skin texture, and facial structure.
Using Image 4 for body proportions, body type, and physique.

Generate a hyper-realistic photograph of a young woman:
- Pose: Replicate the exact pose, body position, and camera angle from Image 1. Keep the clothing style - cropped black top with white collar, matching outfit aesthetic.
- Hairstyle: Keep the exact hairstyle from Image 1 - long hair styled in pigtails.
- Background: Use the exact room layout from Image 2 - luxury living room with black leather tufted sofa on LEFT side, hardwood floors, hallway with dark wooden doors visible behind (NOT a kitchen), warm ambient cove lighting.
- Face: Take exact facial features from Image 3 - the olive-brown eyes, natural skin texture with visible pores, subtle freckles, dark brown hair color, and facial bone structure. Preserve all minor skin imperfections and realistic skin details.
- Body: Apply the slim petite body type from Image 4 - extremely thin slender frame, very narrow tiny waist, slim hips, long thin legs.

Style: Shot on Canon EOS R5, 85mm f/1.4 lens, shallow depth of field, professional fashion photography.
Skin: Hyper-realistic with natural texture, visible pores, subtle imperfections, minor skin flaws for authenticity.
Lighting: Warm natural light from Image 2 environment.

Keep pose, outfit and hairstyle from Image 1.
Preserve background layout from Image 2 unchanged, sofa on left side.
Preserve facial identity from Image 3 unchanged.
Preserve body proportions from Image 4 unchanged."""


def encode_image(path: str) -> str:
    """Encode image to base64 data URI"""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/png")
    return f"data:{mime};base64,{data}"


async def transform_with_multi_ref():
    """Transform using SEEDream 4.5 with 4 reference images"""
    
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not configured")
        return None
    
    print("Encoding 4 reference images...")
    pose_b64 = encode_image(POSE_REF)
    face_b64 = encode_image(FACE_REF)
    body_b64 = encode_image(BODY_REF)
    bg_b64 = encode_image(BG_REF)
    
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": MULTI_REF_PROMPT,
        "image_urls": [pose_b64, bg_b64, face_b64, body_b64],
        "image_size": {"width": 1080, "height": 1350},
        "num_images": 1,
        "max_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": "cartoon, anime, illustration, painting, blue eyes, grey eyes, black hair, wavy hair, curly hair, extra limbs, deformed, blurry skin, plastic skin, airbrushed, overly smooth skin"
    }
    
    print("="*60)
    print("SEEDream 4.5 Multi-Reference Transformation")
    print("="*60)
    print("Image 1: Pose/outfit reference")
    print("Image 2: Background reference (MEDIUM PRIORITY)")
    print("Image 3: Face reference (Starbright)")
    print("Image 4: Body reference (Starbright)")
    print("="*60)
    print("Sending request...")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                FAL_SEEDREAM_URL,
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
                        print("Downloading generated image...")
                        img_resp = await client.get(img_url)
                        if img_resp.status_code == 200:
                            Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"starbright_multiref_{timestamp}.png"
                            filepath = Path(OUTPUT_DIR) / filename
                            filepath.write_bytes(img_resp.content)
                            
                            print(f"SUCCESS! Image saved: {filepath}")
                            return str(filepath)
                
                print("ERROR: No images in response")
                print(result)
                return None
            
            else:
                print(f"API error {response.status_code}: {response.text[:1000]}")
                return None
                
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None


if __name__ == "__main__":
    result = asyncio.run(transform_with_multi_ref())
    if result:
        print(f"\nMulti-reference transformation complete! Output: {result}")
    else:
        print("\nTransformation failed.")
