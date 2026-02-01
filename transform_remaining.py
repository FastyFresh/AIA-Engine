"""Transform remaining images"""
import asyncio
import sys
import os
from pathlib import Path
import base64
import httpx

sys.path.insert(0, '.')

FAL_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{data}"

async def transform_image(source_path: str, output_path: str, fal_key: str) -> dict:
    source_uri = encode_image(source_path)
    face_uri = encode_image("content/references/starbright_monroe/starbright_face_reference_v3.webp")
    body_uri = encode_image("content/references/starbright_monroe/body_reference.webp")
    
    prompt = """Transform the person in Figure 1 to match the face of Figure 2 and body proportions of Figure 3.
Figure 2 identity: Young woman with delicate symmetrical face, large round hazel-green eyes, natural arched eyebrows, small nose, full natural lips, light freckles across cheeks, high cheekbones, smooth skin, long straight honey-brown hair
Figure 3 body: slim healthy petite body, natural proportions, small A-cup chest
Preserve the exact pose, clothing, setting, and lighting from Figure 1."""

    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "image_urls": [source_uri, face_uri, body_uri],
        "image_size": "auto_4K",
        "num_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": "distorted face, different person, changed clothing, changed background, skeletal"
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(FAL_EDIT_URL, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])
            if images:
                img_url = images[0].get("url", "")
                if img_url:
                    img_resp = await client.get(img_url)
                    if img_resp.status_code == 200:
                        Path(output_path).write_bytes(img_resp.content)
                        return {"status": "success"}
        return {"status": "error"}

async def main():
    fal_key = os.getenv("FAL_KEY", "")
    input_dir = Path("content/transform_input/012426transform 4")
    output_dir = Path("content/transformed/starbright_monroe")
    
    # Find remaining images
    all_sources = set(p.stem for p in input_dir.glob("*.jpg"))
    done = set(p.stem.replace("transformed_", "") for p in output_dir.glob("*.png"))
    remaining = all_sources - done
    
    print(f"Remaining: {len(remaining)} images")
    for name in remaining:
        src = input_dir / f"{name}.jpg"
        out = output_dir / f"transformed_{name}.png"
        print(f"Transforming: {name}")
        result = await transform_image(str(src), str(out), fal_key)
        print(f"  {result['status']}")

asyncio.run(main())
