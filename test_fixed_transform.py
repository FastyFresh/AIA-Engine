"""
Test the FIXED transform_image method with source image included
"""
import asyncio
import sys
import shutil
from pathlib import Path

sys.path.insert(0, '.')

from app.services.seedream4_service import Seedream4Service

GALLERY_PATH = Path("content/generated/starbright_monroe")

async def main():
    GALLERY_PATH.mkdir(parents=True, exist_ok=True)
    
    service = Seedream4Service(influencer_id="starbright_monroe")
    
    test_images = [
        "content/transform_input/012426transform 4/SnapInsta.to_603828247_17866939128519906_3556279129994261783_n.jpg",
        "content/transform_input/012426transform 4/SnapInsta.to_561304697_17859335226513804_912803480032312286_n.jpg"
    ]
    
    prompt = """Young woman with very pale porcelain ivory white skin, straight sleek dark brown hair,
warm hazel-brown eyes, natural freckles across nose and cheeks.
Natural skin texture with visible pores, photorealistic.
Shot on Canon EOS R5, 85mm f/1.4 lens, 8K ultra detailed."""

    print("Testing FIXED transform_image with source image included")
    print("="*60)
    
    for src_path in test_images:
        src = Path(src_path)
        print(f"\nTransforming: {src.name[:40]}...")
        
        result = await service.transform_image(
            source_image_path=str(src),
            prompt=prompt,
            aspect_ratio="3:4",
            seed=42,
            filename_prefix="fixed_transform",
            size="4K"
        )
        
        print(f"  Status: {result.get('status')}")
        if result.get('error'):
            print(f"  Error: {result.get('error')}")
        
        if result["status"] == "success":
            out_path = result.get("image_path")
            gallery = GALLERY_PATH / f"fixed_{src.stem[:30]}.png"
            shutil.copy2(out_path, gallery)
            print(f"  Gallery: {gallery.name}")

asyncio.run(main())
