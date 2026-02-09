import asyncio
import sys
import os
import httpx
import fal_client
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FAL_ENDPOINT = "fal-ai/bytedance/seedream/v4.5/edit"

async def main():
    face_ref = "content/references/starbright_monroe/starbright_face_reference_v3.png"
    body_ref = "content/references/starbright_monroe/body_reference_blue_upscaled.png"
    source_image = "content/sources/starbright_monroe/hellokitty_bikini_source.jpg"
    
    print("Uploading references...")
    face_url = fal_client.upload_file(face_ref)
    body_url = fal_client.upload_file(body_ref)
    source_url = fal_client.upload_file(source_image)
    
    identity = (
        "naturally fair light skin with a healthy warm undertone and visible pores, "
        "straight sleek dark brown hair past shoulders with natural flyaway strands, "
        "distinctive warm olive-brown hazel eyes with natural catchlight reflections, "
        "prominent visible natural freckles scattered across nose bridge and upper cheeks, "
        "very petite slim boyish straight figure like a young ballet dancer with no prominent curves, "
        "thin delicate frame"
    )
    
    backgrounds = [
        {
            "name": "fal_fullbody_bedroom",
            "bg": "standing barefoot in a bright minimalist white bedroom, sheer curtains with soft natural daylight streaming through, white bedding visible behind, warm natural window light with soft shadows"
        },
        {
            "name": "fal_fullbody_balcony",
            "bg": "standing barefoot on a sunlit apartment balcony, soft golden hour morning light, city skyline blurred in background, warm natural sunlight"
        },
        {
            "name": "fal_fullbody_studio",
            "bg": "standing barefoot in a professional photography studio, clean white seamless backdrop, soft diffused studio lighting, warm neutral lighting"
        },
        {
            "name": "fal_fullbody_bathroom",
            "bg": "standing barefoot on white marble floor in a bright luxury bathroom, large mirror and white tiles visible, soft warm overhead lighting with natural light from frosted window"
        },
    ]
    
    output_dir = Path("content/seedream4_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for bg in backgrounds:
        prompt = (
            f"Figure 1 face identity, Figure 2 body proportions, Figure 3 exact pose and outfit. "
            f"Full body photograph from head to bare feet of a 19-year-old woman with {identity}, "
            f"bare ears with absolutely no earrings no jewelry no accessories on ears, "
            f"wearing the exact same Hello Kitty bikini outfit as Figure 3 with cat ear headband, "
            f"{bg['bg']}. "
            f"Full body shot showing entire figure from top of head to toes, "
            f"RAW photo, unretouched, real human skin with visible pores, "
            f"shot on Canon EOS R5, 35mm f/1.4 lens, natural skin texture, 8K detail, photorealistic"
        )
        
        print(f"\n{'='*60}")
        print(f"Generating: {bg['name']}")
        print(f"{'='*60}")
        
        try:
            result = fal_client.subscribe(
                FAL_ENDPOINT,
                arguments={
                    "prompt": prompt,
                    "image_urls": [face_url, body_url, source_url],
                },
                with_logs=True,
            )
            
            images = result.get("images", [])
            if images:
                img_url = images[0].get("url", "")
                if img_url:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        img_resp = await client.get(img_url)
                        if img_resp.status_code == 200:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            save_path = output_dir / f"{bg['name']}_{timestamp}.png"
                            with open(save_path, "wb") as f:
                                f.write(img_resp.content)
                            print(f"SUCCESS: {save_path}")
                        else:
                            print(f"Download failed: {img_resp.status_code}")
                else:
                    print(f"No URL: {images[0]}")
            else:
                print(f"No images: {result}")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
