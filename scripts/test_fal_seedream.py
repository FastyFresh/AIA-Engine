import asyncio
import sys
import os
import httpx
import fal_client
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FAL_ENDPOINT = "fal-ai/bytedance/seedream/v4.5/edit"

async def upload_to_fal(file_path: str) -> str:
    url = fal_client.upload_file(file_path)
    print(f"  Uploaded: {os.path.basename(file_path)} -> {url[:80]}...")
    return url

async def main():
    fal_key = os.getenv("FAL_KEY", "")
    if not fal_key:
        print("ERROR: FAL_KEY not set")
        return
    
    face_ref = "content/references/starbright_monroe/starbright_face_reference_v3.png"
    body_ref = "content/references/starbright_monroe/body_reference_blue_upscaled.png"
    source_image = "content/sources/starbright_monroe/hellokitty_bikini_source.jpg"
    
    print("Uploading reference images to Fal.ai storage...")
    face_url = await upload_to_fal(face_ref)
    body_url = await upload_to_fal(body_ref)
    source_url = await upload_to_fal(source_image)
    
    identity = (
        "extremely pale porcelain ivory white cool-toned skin with visible pores and subtle skin imperfections, "
        "straight sleek dark brown hair past shoulders with natural flyaway strands, "
        "distinctive warm olive-brown hazel eyes with natural catchlight reflections, "
        "prominent visible natural freckles scattered across nose bridge and upper cheeks, "
        "very petite slim boyish straight figure like a young ballet dancer with no prominent curves, "
        "thin delicate frame"
    )
    
    backgrounds = [
        {
            "name": "fal_studio_v1",
            "bg": "standing in a professional photography studio, clean white seamless backdrop, soft diffused studio lighting from above, overcast cool neutral lighting"
        },
        {
            "name": "fal_bedroom_v1",
            "bg": "standing in a bright minimalist white bedroom, sheer curtains with soft natural daylight streaming through, white bedding visible behind, cool overcast soft daylight"
        },
    ]
    
    output_dir = Path("content/seedream4_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for bg in backgrounds:
        prompt = (
            f"Figure 1 face identity, Figure 2 body proportions, Figure 3 exact pose and outfit. "
            f"A 19-year-old woman with {identity}, "
            f"bare ears with absolutely no earrings no jewelry no accessories on ears, "
            f"wearing the exact same Hello Kitty bikini outfit as Figure 3 with cat ear headband, "
            f"{bg['bg']}. "
            f"RAW photo, unretouched, real human skin with visible pores, "
            f"shot on Canon EOS R5, 85mm f/1.4 lens, natural skin texture, 8K detail, photorealistic"
        )
        
        print(f"\n{'='*60}")
        print(f"Generating via Fal.ai: {bg['name']}")
        print(f"{'='*60}")
        
        try:
            def on_queue_update(update):
                if isinstance(update, fal_client.InProgress):
                    for log in update.logs:
                        print(f"  {log.get('message', log)}")
            
            result = fal_client.subscribe(
                FAL_ENDPOINT,
                arguments={
                    "prompt": prompt,
                    "image_urls": [face_url, body_url, source_url],
                },
                with_logs=True,
                on_queue_update=on_queue_update,
            )
            
            print(f"Result keys: {result.keys() if isinstance(result, dict) else type(result)}")
            
            images = result.get("images", [])
            if images:
                img_url = images[0].get("url", "")
                if img_url:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        img_resp = await client.get(img_url)
                        if img_resp.status_code == 200:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"{bg['name']}_{timestamp}.png"
                            save_path = output_dir / filename
                            with open(save_path, "wb") as f:
                                f.write(img_resp.content)
                            print(f"SUCCESS: {save_path}")
                        else:
                            print(f"Failed to download image: {img_resp.status_code}")
                else:
                    print(f"No image URL in result: {images[0]}")
            else:
                print(f"No images in result: {result}")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
