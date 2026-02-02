"""Test with face reference as Figure 1 (highest priority)"""
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
    
    # NEW ORDER: Face first (priority), then body, then pose
    face_uri = encode_image(face_ref)
    body_uri = encode_image(body_ref)
    pose_uri = encode_image(pose_source)
    
    # Face as Figure 1 for highest priority
    image_urls = [face_uri, body_uri, pose_uri]
    
    prompt = """Use the EXACT face from Figure 1 - this is the primary identity reference.
Use the body proportions from Figure 2.
Copy the pose, camera angle, and outfit from Figure 3.

Generate: Young woman with Figure 1's exact face - hazel-brown eyes, soft oval jaw, high cheekbones, full lips with cupid's bow, natural freckles across nose and cheeks.
Hair: Dark brown (rich chocolate), straight, matching Figure 1.
Body: Slim petite healthy from Figure 2, natural A-cup.
Pose: Exact same as Figure 3 - leaning forward, hands resting.
Outfit: White bralette and red shorts exactly as shown in Figure 3.

The face MUST match Figure 1 precisely. Photorealistic, 8K quality, Canon EOS R5, 85mm f/1.4."""

    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    payload = {
        "prompt": prompt,
        "image_urls": image_urls,
        "image_size": "auto_4K",
        "num_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": "blue eyes, green eyes, light hair, blonde, different face, wrong face"
    }
    
    print("Testing with FACE as Figure 1 (highest priority)...")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(FAL_EDIT_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])
            if images:
                img_url = images[0].get("url", "")
                if img_url:
                    img_resp = await client.get(img_url)
                    out_path = Path("content/generated/starbright_monroe/face_first_test.png")
                    out_path.write_bytes(img_resp.content)
                    print(f"SUCCESS: {out_path}")
                    return
        print(f"ERROR: {response.status_code}")
        print(response.text[:300])

asyncio.run(test())
