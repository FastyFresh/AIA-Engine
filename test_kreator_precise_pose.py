"""Test with Kreator Flow style + more precise pose description"""
import asyncio
import os
import sys
import base64
from pathlib import Path
import httpx

sys.path.insert(0, '.')

FAL_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{data}"

async def test():
    fal_key = os.getenv("FAL_KEY", "")
    
    face_ref = "content/references/starbright_monroe/starbright_face_reference_v3.webp"
    body_ref = "content/references/starbright_monroe/body_reference.webp"
    pose_source = "content/transform_input/012426transform 4/SnapInsta.to_603828247_17866939128519906_3556279129994261783_n.jpg"
    
    # Order: face, body, pose
    image_urls = [encode_image(face_ref), encode_image(body_ref), encode_image(pose_source)]
    
    # More precise pose description
    prompt = """A portrait of Starbright, using the EXACT pose from reference3: woman leaning forward with torso bent, hands resting on thighs near knees, head tilted slightly looking up at camera.

Replace the face with facial features from reference1: hazel-brown eyes, full lips with cupid's bow, natural freckles across nose and cheeks, dark brown straight hair.
Replace the body with proportions from reference2: slim petite healthy build, natural A-cup.

KEEP from reference3: The exact body position (leaning forward bent at waist), hand placement on thighs, camera angle from above, indoor room background, white bralette and red shorts with white stripe outfit.

Photorealistic, high detail, sharp focus, 8K quality."""

    negative_prompt = "Original influencer's face, blue eyes, green eyes, black hair, blonde hair, different face, wrong identity, standing upright, selfie pose"

    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    payload = {
        "prompt": prompt,
        "image_urls": image_urls,
        "image_size": "auto_4K",
        "num_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": negative_prompt
    }
    
    print("Testing with precise pose description...")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(FAL_EDIT_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])
            if images:
                img_url = images[0].get("url", "")
                if img_url:
                    img_resp = await client.get(img_url)
                    out_path = Path("content/generated/starbright_monroe/kreator_precise_pose.png")
                    out_path.write_bytes(img_resp.content)
                    print(f"SUCCESS: {out_path}")
                    return
        print(f"ERROR: {response.status_code}")
        print(response.text[:500])

asyncio.run(test())
