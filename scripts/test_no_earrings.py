import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.seedream4_service import Seedream4Service
from app.services.prompt_builder import PromptBuilder

async def main():
    service = Seedream4Service()
    builder = PromptBuilder("starbright_monroe")
    
    source_image = "content/sources/starbright_monroe/hellokitty_bikini_source.jpg"
    identity_block = builder.identity
    
    backgrounds = [
        {
            "name": "studio_v4",
            "bg": "standing in a professional photography studio, clean white seamless backdrop, soft diffused studio lighting from above, overcast cool neutral lighting"
        },
        {
            "name": "bedroom_v4",
            "bg": "standing in a bright minimalist white bedroom, sheer curtains with soft natural daylight streaming through, white bedding visible behind, cool overcast soft daylight"
        },
    ]
    
    for bg in backgrounds:
        full_prompt = (
            f"Figure 1 face identity, Figure 2 body proportions, Figure 3 exact pose and outfit. "
            f"A 19-year-old woman with {identity_block}, "
            f"bare ears with absolutely no earrings no jewelry no accessories on ears, "
            f"wearing the exact same Hello Kitty bikini outfit as Figure 3 with cat ear headband, "
            f"{bg['bg']}. "
            f"Shot on Canon EOS R5, 85mm f/1.4 lens, natural skin texture visible, 8K detail"
        )
        
        print(f"\n{'='*60}")
        print(f"Generating: {bg['name']}")
        print(f"{'='*60}")
        
        result = await service.transform_image(
            source_image_path=source_image,
            prompt=full_prompt,
            aspect_ratio="3:4",
            filename_prefix=f"hellokitty_{bg['name']}",
            size="4K"
        )
        
        if result and result.get("status") == "success":
            print(f"SUCCESS: {result.get('output_path', result)}")
        else:
            print(f"RESULT: {result}")

if __name__ == "__main__":
    asyncio.run(main())
