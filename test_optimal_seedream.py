"""
Test Seedream 4.5 with optimal multi-reference prompting
Based on official documentation research

References:
- Figure 1: Pose/outfit source image
- Figure 2: Starbright face reference
- Figure 3: Starbright body reference

Prompt Structure:
1. Reference assignments
2. Subject description with specific facial features
3. Preservation rules
4. Style/lighting/camera
"""
import asyncio
import os
import sys
import base64
import shutil
from pathlib import Path
import httpx

sys.path.insert(0, '.')

FAL_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"
GALLERY_PATH = Path("content/generated/starbright_monroe")

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{data}"

def build_optimal_prompt(pose_description: str = "leaning forward, looking at camera") -> str:
    """Build optimal Seedream 4.5 prompt with Figure references"""
    
    prompt = f"""Use Figure 1 for the exact pose, camera angle, and outfit.
Use Figure 2 for the face and facial features.
Use Figure 3 for the body proportions and physique.

Generate a photorealistic portrait of a young woman:
- Face: Use Figure 2's exact facial structure - soft oval jaw, high cheekbones, hazel-brown eyes, natural freckles across nose and cheeks, full lips with cupid's bow
- Hair: Dark brown (rich chocolate), matching Figure 2
- Body: Slim petite healthy physique from Figure 3, natural A-cup proportions
- Pose: Replicate exact pose from Figure 1 - {pose_description}
- Outfit: Wear the exact same clothing shown in Figure 1

Maintain strict consistency with reference faces. 
Photorealistic style, natural skin texture with visible pores, 8K quality.
Shot on Canon EOS R5, 85mm f/1.4 lens, shallow depth of field."""

    return prompt

async def test_generation():
    fal_key = os.getenv("FAL_KEY", "")
    if not fal_key:
        print("ERROR: FAL_KEY not set")
        return
    
    GALLERY_PATH.mkdir(parents=True, exist_ok=True)
    
    # Reference images
    face_ref = "content/references/starbright_monroe/starbright_face_reference_v3.webp"
    body_ref = "content/references/starbright_monroe/body_reference.webp"
    pose_source = "content/transform_input/012426transform 4/SnapInsta.to_603828247_17866939128519906_3556279129994261783_n.jpg"
    
    print("Loading references...")
    pose_uri = encode_image(pose_source)
    face_uri = encode_image(face_ref)
    body_uri = encode_image(body_ref)
    
    # Order: Figure 1 = pose, Figure 2 = face, Figure 3 = body
    image_urls = [pose_uri, face_uri, body_uri]
    
    prompt = build_optimal_prompt("leaning forward with hands resting, looking directly at camera")
    
    print("\n--- OPTIMAL PROMPT ---")
    print(prompt[:600])
    print("...")
    
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "image_urls": image_urls,
        "image_size": "auto_4K",
        "num_images": 1,
        "max_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": "blue eyes, green eyes, light hair, blonde, skeletal, anorexic, cartoon, illustration, anime, multiple people, wrong eye color"
    }
    
    print("\nGenerating with fal.ai Seedream 4.5...")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(FAL_EDIT_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])
            
            if images:
                img_url = images[0].get("url", "")
                if img_url:
                    img_resp = await client.get(img_url)
                    if img_resp.status_code == 200:
                        out_path = GALLERY_PATH / "optimal_test_v1.png"
                        out_path.write_bytes(img_resp.content)
                        print(f"SUCCESS! Saved: {out_path}")
                        return str(out_path)
        else:
            print(f"ERROR: {response.status_code}")
            print(response.text[:500])
    
    return None

asyncio.run(test_generation())
