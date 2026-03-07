#!/usr/bin/env python3
"""
SFW Identity Test — Seedream 5.0 Lite vs 4.5
Generate SFW test images to evaluate face/body match to Starbright references.
"""
import asyncio, sys, os, json, base64, httpx
from pathlib import Path
from datetime import datetime

sys.path.append("/root/aia-engine/app")
from dotenv import load_dotenv
load_dotenv("/root/aia-engine/.env")

FAL_SEEDREAM5_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v5/lite/edit"
FAL_SEEDREAM5_T2I_URL = "https://fal.run/fal-ai/bytedance/seedream/v5/lite"
FAL_SEEDREAM45_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

REFS_DIR = Path("/root/aia-engine/content/references/starbright_monroe/advanced")
OUTPUT_DIR = Path("/root/aia-engine/content/generated/starbright_monroe/sfw_test")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load identity spec
with open("/root/aia-engine/content/references/starbright_monroe/identity_spec.json") as f:
    spec = json.load(f)

frags = spec["prompt_fragments"]
IDENTITY = frags["identity_core"]
CAMERA = frags["camera_default"]
SKIN = frags["skin_realism"]
QUALITY = frags["quality_default"]

NEGATIVE = (
    "smooth skin, plastic skin, airbrushed, poreless, beauty filter, over-smoothed, "
    "idealized fabric, glossy, CGI, unnatural perfection, symmetrical face, "
    "perfect symmetry, flawless skin, stock photo, 3D render, digital art, "
    "illustration, anime, nudity, nsfw, naked"
)

def image_to_data_uri(path):
    p = Path(path)
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime = mime_map.get(p.suffix.lower(), "image/jpeg")
    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"

# Reference images
face_uri = image_to_data_uri(REFS_DIR / "01_face_front.jpg")
eyes_uri = image_to_data_uri(REFS_DIR / "03_eyes_freckles_enhanced.jpg")
body_uri = image_to_data_uri(REFS_DIR / "05b_body_front_casual.jpg")

print(f"[REFS] Loaded 3 references")

# SFW test scenes
SFW_SCENES = [
    # Scene 0: Close portrait - tests FACE match
    "close-up portrait, soft smile, looking directly at camera, white studio background, "
    "soft diffused lighting, head and shoulders framing",
    
    # Scene 1: Casual full-body - tests BODY match
    "full body photo, fitted sundress, barefoot in grass, golden hour backlight, "
    "hair blowing, candid moment, warm natural tones",
    
    # Scene 2: Upper body casual - tests face+upper body
    "upper body photo, cropped tank top and jeans, sitting on kitchen counter, "
    "morning coffee in hand, sunny kitchen, casual lifestyle photography",
    
    # Scene 3: Full body bikini - tests body proportions
    "full body photo, white triangle bikini, standing by pool edge, bright sunlight, "
    "water reflections, summer vibes, natural relaxed pose",
]


async def generate_edit(prompt, refs, endpoint, label, idx):
    """Generate via Seedream Edit endpoint."""
    fal_key = os.getenv("FAL_KEY", "")
    payload = {
        "prompt": prompt,
        "image_urls": refs,
        "image_size": "auto_3K",
        "num_images": 1,
        "max_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": NEGATIVE,
    }
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json",
    }
    
    t0 = datetime.now()
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(endpoint, headers=headers, json=payload)
        elapsed = (datetime.now() - t0).total_seconds()
        
        if resp.status_code != 200:
            print(f"  [{label}] ERROR {resp.status_code}: {resp.text[:200]}")
            return None
        
        data = resp.json()
        images = data.get("images", [])
        if not images:
            print(f"  [{label}] No images returned")
            return None
        
        img_url = images[0].get("url", "")
        fname = f"{label}_scene{idx}_{datetime.now().strftime('%H%M%S')}.png"
        fpath = OUTPUT_DIR / fname
        
        # Download the image
        async with httpx.AsyncClient(timeout=60.0) as client:
            img_resp = await client.get(img_url)
        with open(fpath, "wb") as f:
            f.write(img_resp.content)
        
        size_mb = len(img_resp.content) / 1024 / 1024
        print(f"  [{label}] Scene {idx}: {fpath.name} ({size_mb:.1f}MB, {elapsed:.1f}s)")
        return str(fpath)
    
    except Exception as e:
        elapsed = (datetime.now() - t0).total_seconds()
        print(f"  [{label}] ERROR after {elapsed:.1f}s: {e}")
        return None


async def generate_t2i(prompt, endpoint, label, idx):
    """Generate via Seedream T2I (text-only, no refs)."""
    fal_key = os.getenv("FAL_KEY", "")
    payload = {
        "prompt": prompt,
        "image_size": "auto_3K",
        "num_images": 1,
        "max_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": NEGATIVE,
    }
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json",
    }
    
    t0 = datetime.now()
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(endpoint, headers=headers, json=payload)
        elapsed = (datetime.now() - t0).total_seconds()
        
        if resp.status_code != 200:
            print(f"  [{label}] ERROR {resp.status_code}: {resp.text[:200]}")
            return None
        
        data = resp.json()
        images = data.get("images", [])
        if not images:
            print(f"  [{label}] No images returned")
            return None
        
        img_url = images[0].get("url", "")
        fname = f"{label}_scene{idx}_{datetime.now().strftime('%H%M%S')}.png"
        fpath = OUTPUT_DIR / fname
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            img_resp = await client.get(img_url)
        with open(fpath, "wb") as f:
            f.write(img_resp.content)
        
        size_mb = len(img_resp.content) / 1024 / 1024
        print(f"  [{label}] Scene {idx}: {fpath.name} ({size_mb:.1f}MB, {elapsed:.1f}s)")
        return str(fpath)
    
    except Exception as e:
        elapsed = (datetime.now() - t0).total_seconds()
        print(f"  [{label}] ERROR after {elapsed:.1f}s: {e}")
        return None


async def main():
    scene_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    scene = SFW_SCENES[scene_idx]
    
    # Build prompts
    prompt_3ref = (
        f"Use the woman from Figure 1 (face reference) with the eye color and freckle pattern "
        f"from Figure 2, and the body proportions from Figure 3 (body reference). "
        f"Maintain her EXACT facial features: {IDENTITY}. "
        f"{scene}. "
        f"{SKIN}. {CAMERA}, {QUALITY}"
    )
    
    prompt_2ref = (
        f"Use the woman from Figure 1 (face reference) and Figure 2 (body reference). "
        f"Maintain her EXACT facial features: {IDENTITY}. "
        f"{scene}. "
        f"{SKIN}. {CAMERA}, {QUALITY}"
    )
    
    prompt_t2i = (
        f"Photo of a young woman, {IDENTITY}. "
        f"{scene}. "
        f"{SKIN}. {CAMERA}, {QUALITY}"
    )
    
    refs_3 = [face_uri, eyes_uri, body_uri]
    refs_2 = [face_uri, body_uri]
    
    print(f"\n{'='*60}")
    print(f"SFW IDENTITY TEST — Scene {scene_idx}")
    print(f"{'='*60}")
    print(f"Scene: {scene[:80]}...")
    print()
    
    results = {}
    
    # Test 1: Seedream 5.0 Lite Edit with 3 refs
    print("[1/4] Seedream 5.0 Lite Edit — 3 refs (face + eyes + body)...")
    r = await generate_edit(prompt_3ref, refs_3, FAL_SEEDREAM5_EDIT_URL, "sd5_3ref", scene_idx)
    results["sd5_3ref"] = r
    
    # Test 2: Seedream 5.0 Lite Edit with 2 refs
    print("[2/4] Seedream 5.0 Lite Edit — 2 refs (face + body)...")
    r = await generate_edit(prompt_2ref, refs_2, FAL_SEEDREAM5_EDIT_URL, "sd5_2ref", scene_idx)
    results["sd5_2ref"] = r
    
    # Test 3: Seedream 4.5 Edit with 2 refs
    print("[3/4] Seedream 4.5 Edit — 2 refs (face + body)...")
    r = await generate_edit(prompt_2ref, refs_2, FAL_SEEDREAM45_EDIT_URL, "sd45_2ref", scene_idx)
    results["sd45_2ref"] = r
    
    # Test 4: Seedream 5.0 Lite T2I (no refs, prompt only)
    print("[4/4] Seedream 5.0 Lite T2I — text only (no refs)...")
    r = await generate_t2i(prompt_t2i, FAL_SEEDREAM5_T2I_URL, "sd5_t2i", scene_idx)
    results["sd5_t2i"] = r
    
    print(f"\n{'='*60}")
    print("RESULTS:")
    for k, v in results.items():
        status = "✓" if v else "✗"
        print(f"  {status} {k}: {v or 'FAILED'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
