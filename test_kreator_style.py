"""Test with Kreator Flow style prompt structure"""
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
    
    # Order: face, body, pose (reference1, reference2, reference3)
    face_uri = encode_image(face_ref)
    body_uri = encode_image(body_ref)
    pose_uri = encode_image(pose_source)
    
    image_urls = [face_uri, body_uri, pose_uri]
    
    # Kreator Flow style prompt
    prompt = """A unique portrait of Starbright as a confident woman, using the exact dynamic pose, arm positions, and look from reference3, but with the facial features, expression, hazel-brown eyes, full lips, natural freckles, and dark brown hair from reference1, and body proportions, slim petite build, and skin tone from reference2.

Keep the white bralette and red shorts outfit from reference3.
Keep the indoor room setting and camera angle from reference3.
Cinematic lighting, photorealistic style, high detail, sharp focus, 8K quality."""

    negative_prompt = "Original influencer's face or body, blue eyes, green eyes, blonde hair, light hair, different face, wrong identity, low quality, distortions"

    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    payload = {
        "prompt": prompt,
        "image_urls": image_urls,
        "image_size": "auto_4K",
        "num_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": negative_prompt
    }
    
    print("Testing with Kreator Flow style prompt...")
    print(f"Prompt:\n{prompt}\n")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(FAL_EDIT_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])
            if images:
                img_url = images[0].get("url", "")
                if img_url:
                    img_resp = await client.get(img_url)
                    out_path = Path("content/generated/starbright_monroe/kreator_style_test.png")
                    out_path.write_bytes(img_resp.content)
                    print(f"SUCCESS: {out_path}")
                    return
        print(f"ERROR: {response.status_code}")
        print(response.text[:500])

asyncio.run(test())
