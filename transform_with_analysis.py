"""Transform images with Grok background analysis"""
import asyncio
import sys
import os
from pathlib import Path
import base64
import json
import httpx

sys.path.insert(0, '.')
from app.services.background_analyzer import BackgroundAnalyzer, BACKGROUND_PRESETS

FAL_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{data}"

async def transform_image(source_path: str, output_path: str, background_desc: str, fal_key: str) -> dict:
    source_uri = encode_image(source_path)
    face_uri = encode_image("content/references/starbright_monroe/starbright_face_reference_v3.webp")
    body_uri = encode_image("content/references/starbright_monroe/body_reference.webp")
    
    prompt = f"""Transform the person in Figure 1 to match Figure 2 (face) and Figure 3 (body).

REQUIRED CHANGES:
- Face: Match Figure 2 exactly - delicate symmetrical face, large round hazel-green eyes, natural arched eyebrows, small nose, full natural lips, light freckles across cheeks, high cheekbones
- Hair: MUST be long straight honey-brown hair (NOT black, NOT dark, NOT short)
- Body: slim healthy petite body, natural proportions, small A-cup chest like Figure 3
- Background: Replace with {background_desc}

PRESERVE from Figure 1:
- Exact pose and body position
- Clothing/outfit style and colors
- Facial expression and mood"""

    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "image_urls": [source_uri, face_uri, body_uri],
        "image_size": "auto_4K",
        "num_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": "black hair, dark hair, short hair, different face, skeletal"
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
        return {"status": "error"}

async def main():
    fal_key = os.getenv("FAL_KEY", "")
    analyzer = BackgroundAnalyzer()
    
    # Test with 3 images
    test_images = [
        "content/transform_input/012426transform 4/SnapInsta.to_603828247_17866939128519906_3556279129994261783_n.jpg",
        "content/transform_input/012426transform 4/SnapInsta.to_398602122_325603090216830_2559318016282510058_n.jpg",
        "content/transform_input/012426transform 4/SnapInsta.to_561304697_17859335226513804_912803480032312286_n.jpg"
    ]
    
    output_dir = Path("content/transformed/starbright_monroe_v3")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for src_path in test_images:
        src = Path(src_path)
        print(f"\n--- Analyzing: {src.name} ---")
        
        # Step 1: Analyze background with Grok
        analysis = analyzer.analyze_background(str(src))
        matched = analysis.get("matched_preset", "apartment_bedroom_day")
        bg_desc = analysis.get("preset_description", BACKGROUND_PRESETS["apartment_bedroom_day"]["description"])
        
        print(f"  Original: {analysis.get('background_description', 'unknown')}")
        print(f"  Matched: {matched}")
        
        # Step 2: Transform with matched background
        out = output_dir / f"v3_{src.stem}.png"
        print(f"  Transforming...")
        result = await transform_image(str(src), str(out), bg_desc, fal_key)
        print(f"  Result: {result['status']}")

asyncio.run(main())
