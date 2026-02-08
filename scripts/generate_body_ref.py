import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.seedream4_service import Seedream4Service

async def main():
    service = Seedream4Service()
    
    identity = (
        "extremely pale porcelain ivory white cool-toned skin, "
        "straight sleek dark brown hair past shoulders, "
        "distinctive warm olive-brown hazel eyes, "
        "prominent visible natural freckles across nose and cheeks, "
        "very petite slim boyish straight figure like a young ballet dancer with no prominent curves, "
        "thin delicate frame, clothing hangs loosely on her thin frame"
    )
    
    variants = [
        {
            "name": "body_ref_crop_top",
            "prompt": (
                f"Figure 1 face identity, Figure 2 body proportions. "
                f"A 19-year-old woman with {identity}, "
                f"bare ears with absolutely no earrings no jewelry, "
                f"wearing a simple white fitted crop top and light grey cotton shorts, "
                f"standing straight facing camera with arms relaxed at sides, "
                f"full body visible head to feet, "
                f"plain white studio backdrop, soft even diffused lighting, "
                f"neutral relaxed expression, "
                f"shot on Canon EOS R5, 85mm f/1.4 lens, natural skin texture, 8K detail"
            ),
        },
        {
            "name": "body_ref_sports_bra",
            "prompt": (
                f"Figure 1 face identity, Figure 2 body proportions. "
                f"A 19-year-old woman with {identity}, "
                f"bare ears with absolutely no earrings no jewelry, "
                f"wearing a simple black sports bra and black athletic leggings, "
                f"standing straight facing camera with arms relaxed at sides, "
                f"full body visible head to feet, "
                f"plain white studio backdrop, soft even diffused lighting, "
                f"neutral relaxed expression, "
                f"shot on Canon EOS R5, 85mm f/1.4 lens, natural skin texture, 8K detail"
            ),
        },
        {
            "name": "body_ref_tank_top",
            "prompt": (
                f"Figure 1 face identity, Figure 2 body proportions. "
                f"A 19-year-old woman with {identity}, "
                f"bare ears with absolutely no earrings no jewelry, "
                f"wearing a fitted ribbed white tank top and denim shorts, "
                f"standing straight facing camera with arms relaxed at sides, "
                f"full body visible head to feet, "
                f"plain white studio backdrop, soft even diffused lighting, "
                f"neutral relaxed expression, "
                f"shot on Canon EOS R5, 85mm f/1.4 lens, natural skin texture, 8K detail"
            ),
        },
    ]
    
    for v in variants:
        print(f"\n{'='*60}")
        print(f"Generating: {v['name']}")
        print(f"{'='*60}")
        
        result = await service.generate(
            prompt=v["prompt"],
            aspect_ratio="3:4",
            filename_prefix=v["name"],
            size="4K"
        )
        
        if result and result.get("status") == "success":
            print(f"SUCCESS: {result.get('image_path')}")
        else:
            print(f"RESULT: {result}")

if __name__ == "__main__":
    asyncio.run(main())
