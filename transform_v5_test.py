"""
Transform V5 Test - Fixed prompt structure, background references, auto-copy to gallery
See docs/starbright_transformation_guide.md for full documentation.
"""
import asyncio
import sys
import os
import shutil
from pathlib import Path
import base64
import json
import httpx

sys.path.insert(0, '.')
from app.services.background_analyzer import BackgroundAnalyzer, BACKGROUND_PRESETS

FAL_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

# Gallery path for all generated images
GALLERY_PATH = Path("content/generated/starbright_monroe")

# Background reference images
BACKGROUND_REFS = {
    "bedroom": "content/references/backgrounds/modern_luxury_bedroom.png",
    "living_room": "content/references/backgrounds/modern_luxury_living_room.png"
}

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{data}"


def build_v5_prompt(background_desc: str) -> str:
    """
    V5 prompt - Clear instruction without Figure numbering that confuses the model.
    Uses image_urls order: [source, face_ref, body_ref]
    """
    prompt = f"""Transform this person into Starbright Monroe:

IDENTITY (apply to the person in the first image):
- Face: Delicate symmetrical features, large round hazel-green eyes, natural arched eyebrows, small nose, full natural lips, light freckles across cheeks, high cheekbones (match the face reference)
- Body: Slim healthy petite body, natural proportions, small A-cup chest (match the body reference - NOT skeletal or underweight)
- Hair: Long honey-brown hair (keep the hairstyle from the original but change color to honey-brown)

PRESERVE from original image:
- Exact pose and body position
- Outfit/clothing style and colors

BACKGROUND:
{background_desc}

Generate ONE photorealistic image of Starbright Monroe in this pose and outfit."""

    return prompt


async def transform_image(source_path: str, output_path: str, background_desc: str, fal_key: str) -> dict:
    source_uri = encode_image(source_path)
    face_uri = encode_image("content/references/starbright_monroe/starbright_face_reference_v3.webp")
    body_uri = encode_image("content/references/starbright_monroe/body_reference.webp")
    
    prompt = build_v5_prompt(background_desc)
    
    negative_prompt = "multiple people, two people, black hair, dark hair, different face, skeletal, underweight, anorexic, too thin, emaciated, bony, combined room, open floor plan, loft with bedroom and living room together"
    
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


def copy_to_gallery(source_path: str, prefix: str = "v5") -> str:
    """Copy generated image to gallery"""
    GALLERY_PATH.mkdir(parents=True, exist_ok=True)
    src = Path(source_path)
    dest = GALLERY_PATH / f"{prefix}_{src.name}"
    shutil.copy2(src, dest)
    print(f"  Copied to gallery: {dest.name}")
    return str(dest)


async def main():
    fal_key = os.getenv("FAL_KEY", "")
    analyzer = BackgroundAnalyzer()
    
    # Ensure gallery exists
    GALLERY_PATH.mkdir(parents=True, exist_ok=True)
    
    # Test with the 3 images
    test_images = [
        "content/transform_input/012426transform 4/SnapInsta.to_603828247_17866939128519906_3556279129994261783_n.jpg",  # White bra + red shorts
        "content/transform_input/012426transform 4/SnapInsta.to_398602122_325603090216830_2559318016282510058_n.jpg",  # Superman shirt
        "content/transform_input/012426transform 4/SnapInsta.to_561304697_17859335226513804_912803480032312286_n.jpg"   # Red lingerie
    ]
    
    output_dir = Path("content/transformed/starbright_monroe_v5")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for src_path in test_images:
        src = Path(src_path)
        print(f"\n{'='*60}")
        print(f"Processing: {src.name}")
        print(f"{'='*60}")
        
        # Step 1: Analyze background with Grok
        print("Step 1: Analyzing with Grok...")
        analysis = analyzer.analyze_background(str(src))
        
        matched = analysis.get("matched_preset", "apartment_bedroom_day")
        bg_desc = analysis.get("preset_description", BACKGROUND_PRESETS["apartment_bedroom_day"]["description"])
        outfit = analysis.get("outfit_type", "")
        override = analysis.get("outfit_override", False)
        
        print(f"  Outfit: {outfit}")
        print(f"  Preset: {matched}" + (" (outfit override)" if override else ""))
        
        # Step 2: Transform with V5 prompt
        out = output_dir / f"v5_{src.stem}.png"
        print(f"\nStep 2: Transforming...")
        result = await transform_image(str(src), str(out), bg_desc, fal_key)
        print(f"  Result: {result['status']}")
        
        # Step 3: Copy to gallery if successful
        gallery_path = None
        if result["status"] == "success":
            gallery_path = copy_to_gallery(str(out), "v5")
        
        results.append({
            "source": src.name,
            "outfit": outfit,
            "matched_preset": matched,
            "override": override,
            "status": result["status"],
            "gallery": gallery_path
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status_icon = "✓" if r["status"] == "success" else "✗"
        print(f"\n{status_icon} {r['source']}:")
        print(f"  Outfit: {r['outfit']}")
        print(f"  Preset: {r['matched_preset']}")
        print(f"  Gallery: {r['gallery'] or 'N/A'}")


asyncio.run(main())
