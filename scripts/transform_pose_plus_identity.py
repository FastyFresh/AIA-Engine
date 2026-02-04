"""
Transform Image using ControlNet (Pose) + IP-Adapter (Face Identity)

Uses fal.ai FLUX with:
- ControlNet pose for exact body positioning from source
- IP-Adapter face for Starbright identity from reference
"""

import os
import base64
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

FAL_FLUX_URL = "https://fal.run/fal-ai/flux-general/image-to-image"

SOURCE_IMAGE = "attached_assets/SnapInsta.to_621833016_17877935706467396_2868144746515660684_n_1770180720096.jpg"
FACE_REF = "content/references/starbright_monroe/starbright_face_reference_v3.webp"
OUTPUT_DIR = "content/seedream4_output"

STARBRIGHT_PROMPT = """young woman with very pale porcelain ivory white skin,
straight sleek dark brown hair parted in middle (not wavy, not curly, not black),
warm olive-brown eyes, natural freckles across nose and cheeks,
extremely thin slender petite body with very narrow tiny waist,
slim narrow hips, long thin slender legs, delicate small frame,
wearing a stylish fitted black mini dress with thin straps, black thigh-high stockings,
in a modern luxury penthouse apartment with floor-to-ceiling windows,
bright natural daylight flooding the room, white marble floors,
contemporary minimalist furniture, elegant sophisticated interior design,
Shot on Canon EOS R5, 85mm f/1.4 lens, shallow depth of field,
natural skin texture with visible pores, subtle imperfections,
professional fashion photography, bright natural lighting, high-key exposure,
8K ultra detailed, photorealistic"""

def encode_image(path: str) -> str:
    """Encode image to base64 data URI"""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    
    ext = Path(path).suffix.lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }.get(ext, "image/png")
    
    return f"data:{mime};base64,{data}"


async def transform_with_pose_and_identity():
    """Transform using ControlNet pose + IP-Adapter face identity"""
    
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not configured")
        return None
    
    print("Encoding images...")
    source_b64 = encode_image(SOURCE_IMAGE)
    face_b64 = encode_image(FACE_REF)
    
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": STARBRIGHT_PROMPT,
        "image_url": source_b64,
        "controlnets": [{
            "path": "pose",
            "control_image_url": source_b64,
            "conditioning_scale": 0.9
        }],
        "ip_adapters": [{
            "path": "https://huggingface.co/XLabs-AI/flux-ip-adapter-v2/resolve/main/ip_adapter.safetensors",
            "image_url": face_b64,
            "scale": 0.8,
            "image_encoder_path": "openai/clip-vit-large-patch14"
        }],
        "num_inference_steps": 30,
        "guidance_scale": 4.0,
        "image_size": {"width": 1024, "height": 1280},
        "enable_safety_checker": False,
        "negative_prompt": "blue eyes, grey eyes, black hair, wavy hair, curly hair, extra limbs, deformed, dark lighting"
    }
    
    print("Sending request to FLUX with ControlNet (pose) + IP-Adapter (face)...")
    print("ControlNet conditioning scale: 0.9 (strong pose adherence)")
    print("IP-Adapter scale: 0.8 (strong face identity)")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                FAL_FLUX_URL,
                headers=headers,
                json=payload
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                images = result.get("images", [])
                
                if images:
                    img_url = images[0].get("url", "")
                    if img_url:
                        print("Downloading generated image...")
                        img_resp = await client.get(img_url)
                        if img_resp.status_code == 200:
                            Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"starbright_pose_identity_{timestamp}.png"
                            filepath = Path(OUTPUT_DIR) / filename
                            filepath.write_bytes(img_resp.content)
                            
                            print(f"SUCCESS! Image saved: {filepath}")
                            return str(filepath)
                
                print("ERROR: No images in response")
                print(result)
                return None
            
            else:
                print(f"API error {response.status_code}: {response.text[:1000]}")
                return None
                
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None


if __name__ == "__main__":
    result = asyncio.run(transform_with_pose_and_identity())
    if result:
        print(f"\nPose + Identity transformation complete! Output: {result}")
    else:
        print("\nTransformation failed.")
