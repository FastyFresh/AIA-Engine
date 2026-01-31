"""
Transform attached images to Starbright Monroe using Replicate Seedream 4.5
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.seedream4_service import Seedream4Service

IMAGES_TO_TRANSFORM = [
    "attached_assets/SnapInsta.to_626054043_17908865850339528_2186702621468230721_n_1769838146231.jpg",
    "attached_assets/SnapInsta.to_620895161_17975511443979286_5117931721265806746_n_1769838146235.jpg"
]

TRANSFORM_PROMPT = """
Young woman with very pale porcelain ivory white skin with natural freckles across nose and cheeks,
straight sleek dark brown hair (not wavy, not curly), warm olive-brown eyes,
extremely thin slender petite body with very narrow tiny waist, slim narrow hips, long thin slender legs,
natural skin texture with visible pores, fine skin detail, slight natural skin imperfections,
photorealistic skin tones, no plastic skin, no airbrushed, no over-smoothed, no beauty filter,
Shot on Canon EOS R5, 85mm f/1.4 lens, 8K ultra detailed, cinematic lighting
"""


async def main():
    print("=" * 60)
    print("Transform Images to Starbright Monroe (Replicate Seedream 4.5)")
    print("=" * 60)
    
    service = Seedream4Service(influencer_id="starbright_monroe")
    
    for i, image_path in enumerate(IMAGES_TO_TRANSFORM, 1):
        if not os.path.exists(image_path):
            print(f"\nImage not found: {image_path}")
            continue
        
        img_name = Path(image_path).stem[:25]
        prefix = f"starbright_transform_{i}"
        
        print(f"\n[{i}/{len(IMAGES_TO_TRANSFORM)}] Transforming: {img_name}...")
        
        result = await service.transform_image(
            source_image_path=image_path,
            prompt=TRANSFORM_PROMPT,
            aspect_ratio="3:4",
            filename_prefix=prefix,
            size="4K"
        )
        
        if result["status"] == "success":
            print(f"  SUCCESS: {result['filename']}")
            print(f"  Saved to: {result['image_path']}")
        else:
            print(f"  FAILED: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print("\nOutput directory: content/seedream4_output/")


if __name__ == "__main__":
    asyncio.run(main())
