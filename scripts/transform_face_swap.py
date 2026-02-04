"""
Two-Step Pipeline: ControlNet Pose -> Face Swap

Step 1: Generate with exact pose using ControlNet
Step 2: Apply Starbright face using IP-Adapter Face ID
"""

import os
import base64
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

FAL_CONTROLNET_URL = "https://fal.run/fal-ai/z-image/turbo/controlnet"
FAL_FACE_SWAP_URL = "https://fal.run/fal-ai/face-swap"

SOURCE_IMAGE = "attached_assets/SnapInsta.to_621833016_17877935706467396_2868144746515660684_n_1770180720096.jpg"
FACE_REF = "content/references/starbright_monroe/starbright_face_reference_v3.webp"
OUTPUT_DIR = "content/seedream4_output"

STARBRIGHT_PROMPT = """young woman with very pale porcelain ivory white skin,
straight sleek dark brown hair (not wavy, not curly),
warm olive-brown eyes, natural freckles across nose and cheeks,
extremely thin slender petite body with very narrow tiny waist,
wearing a stylish fitted black mini dress with thin straps, black thigh-high stockings,
in a modern luxury penthouse apartment with floor-to-ceiling windows,
bright natural daylight flooding the room, white marble floors,
Shot on Canon EOS R5, 85mm f/1.4 lens, shallow depth of field,
natural skin texture with visible pores,
professional fashion photography, bright natural lighting, 8K ultra detailed"""

def encode_image(path: str) -> str:
    """Encode image to base64 data URI"""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/png")
    return f"data:{mime};base64,{data}"


async def step1_generate_pose():
    """Step 1: Generate with exact pose using ControlNet"""
    fal_key = os.getenv("FAL_KEY")
    source_b64 = encode_image(SOURCE_IMAGE)
    
    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    payload = {
        "prompt": STARBRIGHT_PROMPT,
        "image_url": source_b64,
        "preprocess": "pose",
        "control_strength": 0.95,
        "num_images": 1,
        "image_size": {"width": 1024, "height": 1280},
        "guidance_scale": 7.5,
        "num_inference_steps": 30,
        "negative_prompt": "blue eyes, grey eyes, extra limbs, deformed, dark lighting",
        "enable_safety_checker": False
    }
    
    print("Step 1: Generating with ControlNet POSE (control_strength=0.95)...")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(FAL_CONTROLNET_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])
            if images:
                img_url = images[0].get("url", "")
                if img_url:
                    print(f"Step 1 SUCCESS! Pose-matched image URL ready")
                    return img_url
        
        print(f"Step 1 FAILED: {response.status_code} - {response.text[:200]}")
        return None


async def step2_face_swap(pose_image_url: str):
    """Step 2: Apply Starbright face using face swap"""
    fal_key = os.getenv("FAL_KEY")
    face_b64 = encode_image(FACE_REF)
    
    headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    
    payload = {
        "base_image_url": pose_image_url,
        "swap_image_url": face_b64,
        "enable_safety_checker": False
    }
    
    print("Step 2: Applying Starbright face via face swap...")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(FAL_FACE_SWAP_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            img_url = result.get("image", {}).get("url", "")
            if img_url:
                img_resp = await client.get(img_url)
                if img_resp.status_code == 200:
                    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"starbright_pose_faceswap_{timestamp}.png"
                    filepath = Path(OUTPUT_DIR) / filename
                    filepath.write_bytes(img_resp.content)
                    print(f"Step 2 SUCCESS! Final image saved: {filepath}")
                    return str(filepath)
        
        print(f"Step 2 FAILED: {response.status_code} - {response.text[:200]}")
        return None


async def run_pipeline():
    """Run the two-step pipeline"""
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not configured")
        return None
    
    print("="*60)
    print("TWO-STEP PIPELINE: ControlNet Pose -> Face Swap")
    print("="*60)
    
    pose_image_url = await step1_generate_pose()
    if not pose_image_url:
        return None
    
    final_result = await step2_face_swap(pose_image_url)
    return final_result


if __name__ == "__main__":
    result = asyncio.run(run_pipeline())
    if result:
        print(f"\nPipeline complete! Output: {result}")
    else:
        print("\nPipeline failed.")
