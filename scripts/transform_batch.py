"""
Batch Transform: Multiple pose references using optimized SEEDream 4.5 workflow

Order: Image 1 (pose) → Image 2 (background) → Image 3 (face) → Image 4 (body)
"""

import os
import base64
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

FAL_SEEDREAM_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

POSE_REFS = [
    "attached_assets/SnapInsta.to_587722373_17847383178618120_1248361727850922868_n_1770183551672.jpg",
    "attached_assets/SnapInsta.to_587287071_17847383166618120_5314159128419985023_n_1770183551673.jpg",
    "attached_assets/SnapInsta.to_584409516_17847383157618120_3128193944047493293_n_1770183551673.jpg"
]

FACE_REF = "attached_assets/starbright_face_reference_v2_1770181950291.webp"
BODY_REF = "attached_assets/body_reference_goal_1770181950292.webp"
BG_REF = "attached_assets/reference,_living_room,_background_1770181950292.png"

OUTPUT_DIR = "content/seedream4_output"

def build_prompt(outfit_desc: str, hairstyle: str = "long straight hair"):
    return f"""Using Image 1 for pose, outfit, hairstyle and camera angle.
Using Image 2 for background environment, room layout, and lighting.
Using Image 3 for facial features, skin texture, and facial structure.
Using Image 4 for body proportions, body type, and physique.

Generate a hyper-realistic photograph of a young woman:
- Pose: Replicate the exact pose, body position, and camera angle from Image 1.
- Outfit: {outfit_desc}
- Hairstyle: Keep {hairstyle} from Image 1.
- Background: Use the exact room layout from Image 2 - luxury living room with black leather tufted sofa on LEFT side, hardwood floors, hallway with dark wooden doors visible behind, warm ambient cove lighting.
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
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/png")
    return f"data:{mime};base64,{data}"


async def transform_single(pose_path: str, index: int, outfit_desc: str, hairstyle: str):
    fal_key = os.getenv("FAL_KEY")
    
    pose_b64 = encode_image(pose_path)
    bg_b64 = encode_image(BG_REF)
    face_b64 = encode_image(FACE_REF)
    body_b64 = encode_image(BODY_REF)
    
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": build_prompt(outfit_desc, hairstyle),
        "image_urls": [pose_b64, bg_b64, face_b64, body_b64],
        "image_size": {"width": 1080, "height": 1388},
        "num_images": 1,
        "max_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": "cartoon, anime, illustration, painting, blue eyes, grey eyes, blonde hair, wavy hair, curly hair, extra limbs, deformed, blurry skin, plastic skin, airbrushed, overly smooth skin"
    }
    
    print(f"\n[Image {index}] Transforming: {Path(pose_path).name}")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(FAL_SEEDREAM_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])
            if images:
                img_url = images[0].get("url", "")
                if img_url:
                    img_resp = await client.get(img_url)
                    if img_resp.status_code == 200:
                        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"starbright_batch_{index}_{timestamp}.png"
                        filepath = Path(OUTPUT_DIR) / filename
                        filepath.write_bytes(img_resp.content)
                        print(f"[Image {index}] SUCCESS: {filepath}")
                        return str(filepath)
        
        print(f"[Image {index}] FAILED: {response.status_code}")
        return None


async def run_batch():
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not configured")
        return
    
    print("="*60)
    print("BATCH TRANSFORMATION - 3 Images")
    print("="*60)
    print("Order: Pose → Background → Face → Body")
    print("="*60)
    
    configs = [
        ("Black long-sleeve crop top with red plaid mini skirt, black choker, white striped thigh-high socks", "long straight hair"),
        ("White v-neck crop top with red plaid mini skirt, black choker", "long straight hair"),
        ("Black v-neck crop top with red plaid mini skirt, black choker, black and white striped thigh-high socks", "long straight hair"),
    ]
    
    results = []
    for i, (pose_path, (outfit, hairstyle)) in enumerate(zip(POSE_REFS, configs), 1):
        result = await transform_single(pose_path, i, outfit, hairstyle)
        results.append(result)
    
    print("\n" + "="*60)
    print("BATCH COMPLETE")
    print("="*60)
    for i, r in enumerate(results, 1):
        status = "SUCCESS" if r else "FAILED"
        print(f"Image {i}: {status}")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_batch())
