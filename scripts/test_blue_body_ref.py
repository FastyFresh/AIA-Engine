import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.seedream4_service import Seedream4Service

async def main():
    service = Seedream4Service()
    
    face_ref = "content/references/starbright_monroe/starbright_face_reference_v3.png"
    body_ref = "content/references/starbright_monroe/body_reference_blue_upscaled.png"
    source_image = "content/sources/starbright_monroe/hellokitty_bikini_source.jpg"
    
    identity = (
        "extremely pale porcelain ivory white cool-toned skin, "
        "straight sleek dark brown hair past shoulders, "
        "distinctive warm olive-brown hazel eyes, "
        "prominent visible natural freckles across nose and cheeks, "
        "very petite slim boyish straight figure like a young ballet dancer with no prominent curves, "
        "thin delicate frame, clothing hangs loosely on her thin frame"
    )
    
    backgrounds = [
        {
            "name": "hellokitty_blue_body_studio_v5",
            "bg": "standing in a professional photography studio, clean white seamless backdrop, soft diffused studio lighting from above, overcast cool neutral lighting"
        },
        {
            "name": "hellokitty_blue_body_bedroom_v5",
            "bg": "standing in a bright minimalist white bedroom, sheer curtains with soft natural daylight streaming through, white bedding visible behind, cool overcast soft daylight"
        },
    ]
    
    for bg in backgrounds:
        full_prompt = (
            f"Figure 1 face identity, Figure 2 body proportions, Figure 3 exact pose and outfit. "
            f"A 19-year-old woman with {identity}, "
            f"bare ears with absolutely no earrings no jewelry no accessories on ears, "
            f"wearing the exact same Hello Kitty bikini outfit as Figure 3 with cat ear headband, "
            f"{bg['bg']}. "
            f"Hyper-realistic photograph, natural skin texture with visible pores and subtle imperfections, "
            f"shot on Canon EOS R5, 85mm f/1.4 lens, 8K detail, photorealistic"
        )
        
        print(f"\n{'='*60}")
        print(f"Generating: {bg['name']}")
        print(f"{'='*60}")
        
        result = await service.transform_image(
            source_image_path=source_image,
            prompt=full_prompt,
            aspect_ratio="3:4",
            filename_prefix=bg["name"],
            size="4K",
            body_ref=body_ref
        )
        
        if result and result.get("status") == "success":
            print(f"SUCCESS: {result.get('output_path', result.get('image_path'))}")
        else:
            print(f"RESULT: {result}")

if __name__ == "__main__":
    asyncio.run(main())
