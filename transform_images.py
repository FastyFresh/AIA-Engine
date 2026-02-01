"""Transform source images into Starbright's likeness"""
import asyncio
import sys
import os
from pathlib import Path
import base64
import httpx

sys.path.insert(0, '.')

FAL_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

def encode_image(path: str) -> str:
    """Encode image to base64 data URI"""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{data}"

async def transform_image(source_path: str, output_path: str, fal_key: str) -> dict:
    """Transform a single image into Starbright's likeness"""
    
    # Encode source image and references
    source_uri = encode_image(source_path)
    face_uri = encode_image("content/references/starbright_monroe/starbright_face_reference_v3.webp")
    body_uri = encode_image("content/references/starbright_monroe/body_reference.webp")
    
    # Prompt to transform the person into Starbright while preserving pose/outfit/setting
    prompt = """Transform the person in Figure 1 to match the face of Figure 2 and body proportions of Figure 3.
    
Figure 2 identity: Young woman with delicate symmetrical face, large round hazel-green eyes, natural arched eyebrows, small nose, full natural lips, light freckles across cheeks, high cheekbones, smooth skin, long straight honey-brown hair, elegant feminine features

Figure 3 body: slim healthy petite body, natural proportions, small A-cup chest

Preserve the exact pose, clothing, setting, and lighting from Figure 1. Only change the person's face and body to match the references. Maintain photorealistic quality."""

    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "image_urls": [source_uri, face_uri, body_uri],
        "image_size": "auto_4K",
        "num_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": "distorted face, different person, changed clothing, changed background, cartoon, anime, skeletal, oversized bust"
    }
    
    try:
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
                            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                            Path(output_path).write_bytes(img_resp.content)
                            return {"status": "success", "output": output_path}
                return {"status": "error", "error": "No images in response"}
            else:
                return {"status": "error", "error": f"API error {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def main():
    fal_key = os.getenv("FAL_KEY", "")
    if not fal_key:
        print("ERROR: FAL_KEY not set")
        return
    
    input_dir = Path("content/transform_input/012426transform 4")
    output_dir = Path("content/transformed/starbright_monroe")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    source_images = list(input_dir.glob("*.jpg"))
    print(f"Found {len(source_images)} images to transform")
    
    for i, src in enumerate(source_images):
        print(f"\n--- Transforming {i+1}/{len(source_images)}: {src.name} ---")
        output_path = output_dir / f"transformed_{src.stem}.png"
        result = await transform_image(str(src), str(output_path), fal_key)
        print(f"Result: {result['status']}")
        if result['status'] == 'error':
            print(f"  Error: {result.get('error', 'unknown')}")

if __name__ == "__main__":
    asyncio.run(main())
