"""
Transform V4 Test - Stronger body reference, pure room backgrounds
See docs/starbright_transformation_guide.md for full documentation.
"""
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


def build_v4_prompt(background_desc: str, outfit_desc: str = "") -> str:
    """Build V4 prompt with stronger body reference enforcement"""
    
    prompt = f"""Generate a photorealistic image using these references:

FIGURE 1 (Source): Copy ONLY the pose, outfit/clothing style, and hairstyle
FIGURE 2 (Face Reference): Use this face EXACTLY - delicate symmetrical features, large round hazel-green eyes, natural arched eyebrows, small nose, full natural lips, light freckles across cheeks, high cheekbones
FIGURE 3 (Body Reference): Use this body type EXACTLY - slim healthy petite body, natural proportions, small A-cup chest

CRITICAL INSTRUCTIONS:
1. Face MUST match Figure 2 exactly
2. Body proportions MUST match Figure 3 exactly - slim healthy petite with natural curves, NOT skeletal or underweight
3. Hair color MUST be honey-brown (copy hairstyle from Figure 1 but change color to honey-brown)
4. Do NOT copy body proportions from Figure 1 - the source model may be too thin
5. Background: {background_desc}

The final image should look like a real person (Figure 2's face + Figure 3's body) in the pose and outfit from Figure 1."""

    return prompt


async def transform_image(source_path: str, output_path: str, background_desc: str, outfit_desc: str, fal_key: str) -> dict:
    source_uri = encode_image(source_path)
    face_uri = encode_image("content/references/starbright_monroe/starbright_face_reference_v3.webp")
    body_uri = encode_image("content/references/starbright_monroe/body_reference.webp")
    
    prompt = build_v4_prompt(background_desc, outfit_desc)
    
    negative_prompt = "black hair, dark hair, different face, skeletal, underweight, anorexic, too thin, emaciated, bony, combined room, open floor plan, loft, living room and bedroom together"
    
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
                        return {"status": "success", "seed": result.get("seed")}
        return {"status": "error", "code": response.status_code}


async def main():
    fal_key = os.getenv("FAL_KEY", "")
    analyzer = BackgroundAnalyzer()
    
    # Test with the 3 problematic images
    test_images = [
        "content/transform_input/012426transform 4/SnapInsta.to_603828247_17866939128519906_3556279129994261783_n.jpg",  # White bra + red shorts
        "content/transform_input/012426transform 4/SnapInsta.to_398602122_325603090216830_2559318016282510058_n.jpg",  # Superman shirt (too thin)
        "content/transform_input/012426transform 4/SnapInsta.to_561304697_17859335226513804_912803480032312286_n.jpg"   # Red lingerie at vanity
    ]
    
    output_dir = Path("content/transformed/starbright_monroe_v4")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for src_path in test_images:
        src = Path(src_path)
        print(f"\n{'='*60}")
        print(f"Processing: {src.name}")
        print(f"{'='*60}")
        
        # Step 1: Analyze background with Grok
        print("Step 1: Analyzing background with Grok...")
        analysis = analyzer.analyze_background(str(src))
        
        matched = analysis.get("matched_preset", "apartment_bedroom_day")
        bg_desc = analysis.get("preset_description", BACKGROUND_PRESETS["apartment_bedroom_day"]["description"])
        outfit = analysis.get("outfit_type", "")
        override = analysis.get("outfit_override", False)
        
        print(f"  Background seen: {analysis.get('background_description', 'unknown')}")
        print(f"  Outfit detected: {outfit}")
        print(f"  Matched preset: {matched}" + (" (outfit override)" if override else ""))
        
        # Step 2: Transform with V4 prompt
        out = output_dir / f"v4_{src.stem}.png"
        print(f"\nStep 2: Transforming with V4 prompt...")
        result = await transform_image(str(src), str(out), bg_desc, outfit, fal_key)
        print(f"  Result: {result['status']}")
        
        results.append({
            "source": src.name,
            "background_seen": analysis.get("background_description"),
            "outfit": outfit,
            "matched_preset": matched,
            "outfit_override": override,
            "transform_status": result["status"]
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for r in results:
        print(f"\n{r['source']}:")
        print(f"  Outfit: {r['outfit']}")
        print(f"  Preset: {r['matched_preset']}" + (" (override)" if r['outfit_override'] else ""))
        print(f"  Status: {r['transform_status']}")


asyncio.run(main())
