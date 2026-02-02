"""
Transform V8 - Uses Seedream 4.5 best practices:
- Locked seed for consistency
- Concrete identity anchors
- Background reference image for consistency
- Low denoise approach
"""
import asyncio
import sys
import os
import shutil
from pathlib import Path
import base64
import httpx

sys.path.insert(0, '.')
from app.services.background_analyzer import BackgroundAnalyzer

FAL_EDIT_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"
GALLERY_PATH = Path("content/generated/starbright_monroe")

# Background reference images for consistency
BACKGROUND_REFS = {
    "bedroom": "content/references/backgrounds/modern_luxury_bedroom.png",
    "living_room": "content/references/backgrounds/modern_luxury_living_room.png"
}

# Locked seed for consistency across all generations
LOCKED_SEED = 42

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{data}"

def build_v8_prompt(room_type: str) -> str:
    """V8 prompt with concrete identity anchors per Seedream 4.5 best practices"""
    
    room_desc = {
        "bedroom": "the luxury bedroom shown in the background reference (Figure 4) - white bed, elegant nightstands, soft morning light",
        "living_room": "the luxury living room shown in the background reference (Figure 4) - black leather sofa, glass coffee table, city view"
    }.get(room_type, "a luxury modern apartment")
    
    return f"""Create a photorealistic photograph.

SUBJECT - Starbright Monroe:
Use the face from Figure 2 and body from Figure 3. Apply these exact features:
- Face: soft oval jaw, high cheekbones, slightly wide-set large hazel-green eyes, small nose with defined bridge, full natural lips with subtle cupid's bow, light freckles across cheeks and nose bridge
- Hair: DARK BROWN color (rich chocolate brown), long, copy only the hairstyle from Figure 1
- Body: slim healthy petite proportions from Figure 3 - natural curves, NOT skeletal, NOT underweight

FROM FIGURE 1 (source) - copy ONLY:
- The exact pose and camera angle
- The clothing/outfit

BACKGROUND:
Place her in {room_desc}

STYLE:
- Real photograph, natural skin texture with pores
- Professional photography with soft natural lighting
- NOT illustration, NOT cartoon, NOT stylized, NOT CGI, NOT digital art"""

async def transform_image(source_path: str, output_path: str, room_type: str, fal_key: str) -> dict:
    source_uri = encode_image(source_path)
    face_uri = encode_image("content/references/starbright_monroe/starbright_face_reference_v3.webp")
    body_uri = encode_image("content/references/starbright_monroe/body_reference.webp")
    
    # Get background reference image
    bg_ref_path = BACKGROUND_REFS.get(room_type, BACKGROUND_REFS["bedroom"])
    bg_uri = encode_image(bg_ref_path)
    
    prompt = build_v8_prompt(room_type)
    negative_prompt = "cartoon, illustration, anime, stylized, digital art, 3d render, cgi, painting, drawing, airbrushed, plastic skin, light hair, blonde, honey hair, reddish hair, auburn, ginger, black hair, skeletal, underweight, anorexic, multiple people, blended face, morphed features"
    
    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "image_urls": [source_uri, face_uri, body_uri, bg_uri],  # 4 reference images
        "image_size": "auto_4K",
        "num_images": 1,
        "enable_safety_checker": False,
        "negative_prompt": negative_prompt,
        "seed": LOCKED_SEED  # Lock seed for consistency
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
        return {"status": "error", "code": getattr(response, 'status_code', 'unknown')}

async def main():
    fal_key = os.getenv("FAL_KEY", "")
    analyzer = BackgroundAnalyzer()
    GALLERY_PATH.mkdir(parents=True, exist_ok=True)
    
    test_images = [
        ("content/transform_input/012426transform 4/SnapInsta.to_603828247_17866939128519906_3556279129994261783_n.jpg", "bedroom"),
        ("content/transform_input/012426transform 4/SnapInsta.to_398602122_325603090216830_2559318016282510058_n.jpg", "living_room"),
        ("content/transform_input/012426transform 4/SnapInsta.to_561304697_17859335226513804_912803480032312286_n.jpg", "bedroom")
    ]
    
    output_dir = Path("content/transformed/starbright_monroe_v8")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Using LOCKED SEED: {LOCKED_SEED}")
    print(f"Using 4 reference images: source, face, body, background\n")
    
    for src_path, room_type in test_images:
        src = Path(src_path)
        print(f"Processing: {src.name}")
        print(f"  Room type: {room_type}")
        print(f"  Background ref: {BACKGROUND_REFS[room_type]}")
        
        out = output_dir / f"v8_{src.stem}.png"
        print("  Transforming with V8 (locked seed, bg reference)...")
        result = await transform_image(str(src), str(out), room_type, fal_key)
        print(f"  Result: {result['status']}")
        
        if result["status"] == "success":
            gallery = GALLERY_PATH / f"v8_{src.stem}.png"
            shutil.copy2(out, gallery)
            print(f"  Gallery: {gallery.name}\n")

asyncio.run(main())
