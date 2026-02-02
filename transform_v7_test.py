"""Transform V7 - Stronger identity enforcement, less cartoonish"""
import asyncio
import sys
import os
import shutil
from pathlib import Path
import base64
import httpx

sys.path.insert(0, '.')
from app.services.background_analyzer import BackgroundAnalyzer, BACKGROUND_PRESETS

FAL_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"
GALLERY_PATH = Path("content/generated/starbright_monroe")

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{data}"

def build_v7_prompt(background_desc: str) -> str:
    """V7 prompt - Photorealistic, strong identity, dark brown hair"""
    return f"""Create a photorealistic photograph of Starbright Monroe in this exact pose and outfit.

PHOTOGRAPHY STYLE:
- Photorealistic, natural skin texture
- Professional photography, NOT illustration, NOT cartoon, NOT stylized
- Natural lighting with realistic shadows

STARBRIGHT MONROE'S APPEARANCE (use the reference images):
- Face: EXACTLY as shown in the face reference - delicate features, large hazel-green eyes, light freckles, high cheekbones. Do NOT blend with the source person's face.
- Hair: DARK BROWN color (like chocolate or espresso), long, styled as shown in source image
- Body: Healthy slim petite figure with natural proportions as shown in body reference. She is NOT underweight or skeletal.

COPY FROM SOURCE IMAGE:
- The exact pose and camera angle
- The clothing/outfit only

SETTING:
{background_desc}

This must look like a real photograph of a real person, not a digital illustration."""

async def transform_image(source_path: str, output_path: str, background_desc: str, fal_key: str) -> dict:
    source_uri = encode_image(source_path)
    face_uri = encode_image("content/references/starbright_monroe/starbright_face_reference_v3.webp")
    body_uri = encode_image("content/references/starbright_monroe/body_reference.webp")
    
    prompt = build_v7_prompt(background_desc)
    negative_prompt = "cartoon, illustration, anime, stylized, digital art, 3d render, cgi, light hair, blonde, honey hair, reddish hair, auburn, ginger, skeletal, underweight, anorexic, emaciated, multiple people, blended face, morphed features"
    
    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "image_urls": [source_uri, face_uri, body_uri],
        "image_size": "auto_4K",
        "num_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": negative_prompt
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
                        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                        Path(output_path).write_bytes(img_resp.content)
                        return {"status": "success"}
        return {"status": "error", "code": getattr(response, 'status_code', 'unknown')}

async def main():
    fal_key = os.getenv("FAL_KEY", "")
    analyzer = BackgroundAnalyzer()
    GALLERY_PATH.mkdir(parents=True, exist_ok=True)
    
    # Test the Superman image
    src_path = "content/transform_input/012426transform 4/SnapInsta.to_398602122_325603090216830_2559318016282510058_n.jpg"
    src = Path(src_path)
    
    print(f"Processing: {src.name}")
    analysis = analyzer.analyze_background(str(src))
    bg_desc = analysis.get("preset_description")
    print(f"  Background: {analysis.get('matched_preset')}")
    
    output_dir = Path("content/transformed/starbright_monroe_v7")
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"v7_{src.stem}.png"
    
    print("  Transforming with V7 prompt (photorealistic focus)...")
    result = await transform_image(str(src), str(out), bg_desc, fal_key)
    print(f"  Result: {result['status']}")
    
    if result["status"] == "success":
        gallery = GALLERY_PATH / f"v7_{src.stem}.png"
        shutil.copy2(out, gallery)
        print(f"  Copied to gallery: {gallery.name}")

asyncio.run(main())
