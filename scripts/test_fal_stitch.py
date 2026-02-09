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
    stitch_source = "content/sources/starbright_monroe/stitch_pajama_source.jpg"
    
    print("Uploading references...")
    face_url = fal_client.upload_file(face_ref)
    body_url = fal_client.upload_file(body_ref)
    stitch_url = fal_client.upload_file(stitch_source)
    
    identity = (
        "naturally fair light skin with a healthy warm undertone and visible pores, "
        "straight sleek dark brown hair past shoulders with natural flyaway strands, "
        "distinctive warm olive-brown hazel eyes with natural catchlight reflections, "
        "prominent visible natural freckles scattered across nose bridge and upper cheeks, "
        "petite slim young woman with a thin frame like a young ballet dancer, "
        "lean toned 19-year-old physique with long legs"
    )
    
    prompt = (
        f"Figure 1 face identity, Figure 2 body proportions, Figure 3 exact pose and outfit. "
        f"Single photograph of one 19-year-old woman, "
        f"NO split screen, NO collage, NO multiple panels, just one single continuous photo. "
        f"She has {identity}, "
        f"she is sitting on a bed playfully holding her hair with one hand, flirty confident expression, "
        f"bare ears with absolutely no earrings no jewelry no accessories on ears, "
        f"wearing the exact same pink Stitch character print long sleeve crop top and matching shorts as Figure 3, "
        f"sitting on a gray bedspread in a cozy dimly lit bedroom, warm moody ambient lighting. "
        f"RAW photo, unretouched, real human skin with visible pores, "
        f"shot on Canon EOS R5, 35mm f/1.4 lens, natural skin texture, 8K detail, photorealistic"
    )
    
    output_dir = Path("content/seedream4_output")
    
    print("\nGenerating: Stitch pajama")
    try:
        result = fal_client.subscribe(
            FAL_ENDPOINT,
            arguments={
                "prompt": prompt,
                "image_urls": [face_url, body_url, stitch_url],
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
                        save_path = output_dir / f"fal_stitch_pajama_v1_{timestamp}.png"
                        with open(save_path, "wb") as f:
                            f.write(img_resp.content)
                        print(f"SUCCESS: {save_path}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
