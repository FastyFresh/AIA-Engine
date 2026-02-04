"""
Batch Transform: SEEDream 4.5 with Consistency Settings

Optimized for consistent face, body, and background across generations.
Uses seed locking, guidance scale, and identity anchors.

Order: Pose (1) → Background (2) → Face (3) → Body (4)
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

LOCKED_SEED = 42
GUIDANCE_SCALE = 5.0

STARBRIGHT_IDENTITY = """oval face shape, high cheekbones, dark brown straight hair, olive-brown eyes, 
natural skin with visible pores and subtle freckles, slim petite frame, very small chest, 
extremely thin slender legs, narrow waist, delicate feminine features"""


def build_prompt(outfit_desc: str, hairstyle: str = "long straight dark brown hair"):
    return f"""Using Image 1 ONLY for pose position and camera angle.
Using Image 2 for background environment, room layout, and lighting.
Using Image 3 for ALL facial features, hair color, and identity.
Using Image 4 for EXACT body proportions.

Generate a hyper-realistic photograph of Starbright Monroe:

CHARACTER IDENTITY (preserve exactly):
{STARBRIGHT_IDENTITY}

INSTRUCTIONS:
- Pose: Take ONLY body position and camera angle from Image 1.
- Background: Use exact room layout from Image 2 - luxury living room with black leather tufted sofa on LEFT side, hardwood floors, warm ambient lighting. Keep background unchanged from Image 2.
- Face & Hair: MUST use Image 3's exact identity - dark brown hair color, olive-brown eyes, natural skin texture with visible pores, subtle freckles, facial bone structure. Hair MUST be dark brown.
- Body: MUST EXACTLY match Image 4's body - very small nearly flat chest, extremely thin slender legs, skinny thighs, narrow waist, petite delicate frame.
- Outfit: {outfit_desc}
- Hairstyle: {hairstyle}

CRITICAL REQUIREMENTS:
- Hair color MUST be dark brown from Image 3, NOT from pose reference.
- Body MUST have small chest and thin legs exactly like Image 4.
- Background MUST match Image 2 layout - sofa on left side.
- Preserve face identity from Image 3 unchanged.

Style: Canon EOS R5, 85mm f/1.4 lens, shallow depth of field, professional fashion photography.
Skin: Hyper-realistic with natural texture, visible pores, subtle imperfections for authenticity."""


def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/png")
    return f"data:{mime};base64,{data}"


async def transform_single(pose_path: str, index: int, outfit_desc: str, hairstyle: str, seed: int = LOCKED_SEED):
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
        "seed": seed,
        "guidance_scale": GUIDANCE_SCALE,
        "enable_safety_checker": False,
        "negative_prompt": "blonde hair, light hair, platinum hair, golden hair, yellow hair, large breasts, big bust, busty, large chest, thick legs, thick thighs, curvy, voluptuous, hourglass figure, wide hips, muscular, athletic, blue eyes, grey eyes, wavy hair, curly hair, cartoon, anime, illustration, plastic skin, airbrushed, overly smooth skin"
    }
    
    print(f"\n[Image {index}] Transforming: {Path(pose_path).name}")
    print(f"[Image {index}] Seed: {seed}, Guidance: {GUIDANCE_SCALE}")
    
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
                        filename = f"starbright_consistent_{index}_{timestamp}.png"
                        filepath = Path(OUTPUT_DIR) / filename
                        filepath.write_bytes(img_resp.content)
                        print(f"[Image {index}] SUCCESS: {filepath}")
                        return str(filepath)
        
        print(f"[Image {index}] FAILED: {response.status_code}")
        try:
            print(f"[Image {index}] Error: {response.text[:500]}")
        except:
            pass
        return None


async def run_batch(seed: int = LOCKED_SEED):
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not configured")
        return
    
    print("="*60)
    print("BATCH TRANSFORMATION - Consistency Mode")
    print("="*60)
    print(f"Seed: {seed} (locked)")
    print(f"Guidance Scale: {GUIDANCE_SCALE}")
    print("Order: Pose → Background → Face → Body")
    print("="*60)
    
    configs = [
        ("Black long-sleeve crop top with red plaid mini skirt, black choker, white striped thigh-high socks", "long straight dark brown hair"),
        ("White v-neck crop top with red plaid mini skirt, black choker", "long straight dark brown hair"),
        ("Black v-neck crop top with red plaid mini skirt, black choker, black and white striped thigh-high socks", "long straight dark brown hair"),
    ]
    
    results = []
    for i, (pose_path, (outfit, hairstyle)) in enumerate(zip(POSE_REFS, configs), 1):
        result = await transform_single(pose_path, i, outfit, hairstyle, seed)
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
