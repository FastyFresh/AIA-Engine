"""
Transform using Replicate's Seedream 4.5
Testing if Replicate handles identity replacement differently than fal.ai
"""
import asyncio
import sys
import os
import shutil
from pathlib import Path
import base64
import httpx
import time

sys.path.insert(0, '.')

REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
SEEDREAM_MODEL = "bytedance/seedream-4.5"
GALLERY_PATH = Path("content/generated/starbright_monroe")

BACKGROUND_REFS = {
    "bedroom": "content/references/backgrounds/modern_luxury_bedroom.png",
    "living_room": "content/references/backgrounds/modern_luxury_living_room.png"
}

LOCKED_SEED = 42

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{data}"

def build_replicate_prompt(room_type: str) -> str:
    room_desc = {
        "bedroom": "luxury modern bedroom with white platform bed, soft morning light",
        "living_room": "luxury penthouse living room with black leather sofa, city skyline view"
    }.get(room_type, "luxury modern apartment")
    
    return f"""Create a photorealistic photograph of a woman.

SUBJECT IDENTITY (from face and body reference images):
- Face: soft oval jaw, high cheekbones, large hazel-brown eyes, small nose, full lips with cupid's bow, light freckles across cheeks and nose
- Hair: DARK BROWN color (rich chocolate brown), long
- Body: slim healthy petite figure, natural proportions, NOT skeletal

COPY FROM SOURCE IMAGE:
- The exact pose and camera angle
- The clothing/outfit

SETTING: {room_desc}

STYLE: Real photograph, natural skin texture, professional photography. NOT cartoon, NOT illustration, NOT CGI."""

async def get_model_version(api_token: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"https://api.replicate.com/v1/models/{SEEDREAM_MODEL}",
            headers={"Authorization": f"Token {api_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("latest_version", {}).get("id")
        raise Exception(f"Failed to get model version: {response.text}")

async def transform_image(source_path: str, output_path: str, room_type: str, api_token: str) -> dict:
    version_id = await get_model_version(api_token)
    
    source_uri = encode_image(source_path)
    face_uri = encode_image("content/references/starbright_monroe/starbright_face_reference_v3.webp")
    body_uri = encode_image("content/references/starbright_monroe/body_reference.webp")
    bg_uri = encode_image(BACKGROUND_REFS[room_type])
    
    prompt = build_replicate_prompt(room_type)
    negative_prompt = "cartoon, illustration, anime, stylized, cgi, light hair, blonde, skeletal, multiple people, blue eyes, green eyes"
    
    headers = {
        "Authorization": f"Token {api_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "version": version_id,
        "input": {
            "prompt": prompt,
            "image_urls": [source_uri, face_uri, body_uri, bg_uri],
            "seed": LOCKED_SEED,
            "negative_prompt": negative_prompt
        }
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Create prediction
        response = await client.post(REPLICATE_API_URL, headers=headers, json=payload)
        
        if response.status_code not in [200, 201]:
            return {"status": "error", "error": f"API error: {response.status_code} - {response.text[:200]}"}
        
        prediction = response.json()
        prediction_id = prediction.get("id")
        
        # Poll for completion
        max_wait = 180
        start = time.time()
        while time.time() - start < max_wait:
            poll_resp = await client.get(
                f"{REPLICATE_API_URL}/{prediction_id}",
                headers=headers
            )
            if poll_resp.status_code == 200:
                status_data = poll_resp.json()
                status = status_data.get("status")
                
                if status == "succeeded":
                    output = status_data.get("output")
                    if output:
                        img_url = output[0] if isinstance(output, list) else output
                        img_resp = await client.get(img_url)
                        if img_resp.status_code == 200:
                            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                            Path(output_path).write_bytes(img_resp.content)
                            return {"status": "success"}
                    return {"status": "error", "error": "No output"}
                    
                elif status == "failed":
                    return {"status": "error", "error": status_data.get("error", "Unknown error")}
                    
            await asyncio.sleep(3)
        
        return {"status": "error", "error": "Timeout"}

async def main():
    api_token = os.getenv("REPLICATE_API_TOKEN", "")
    if not api_token:
        print("ERROR: REPLICATE_API_TOKEN not set")
        return
    
    GALLERY_PATH.mkdir(parents=True, exist_ok=True)
    
    test_images = [
        ("content/transform_input/012426transform 4/SnapInsta.to_603828247_17866939128519906_3556279129994261783_n.jpg", "bedroom"),
        ("content/transform_input/012426transform 4/SnapInsta.to_398602122_325603090216830_2559318016282510058_n.jpg", "living_room"),
        ("content/transform_input/012426transform 4/SnapInsta.to_561304697_17859335226513804_912803480032312286_n.jpg", "bedroom")
    ]
    
    output_dir = Path("content/transformed/starbright_monroe_replicate")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Testing REPLICATE Seedream 4.5")
    print(f"Using LOCKED SEED: {LOCKED_SEED}\n")
    
    for src_path, room_type in test_images:
        src = Path(src_path)
        print(f"Processing: {src.name}")
        print(f"  Room: {room_type}")
        
        out = output_dir / f"replicate_{src.stem}.png"
        print("  Transforming via Replicate...")
        result = await transform_image(str(src), str(out), room_type, api_token)
        print(f"  Result: {result.get('status')}")
        if result.get('error'):
            print(f"  Error: {result.get('error')}")
        
        if result["status"] == "success":
            gallery = GALLERY_PATH / f"replicate_{src.stem}.png"
            shutil.copy2(out, gallery)
            print(f"  Gallery: {gallery.name}\n")

asyncio.run(main())
