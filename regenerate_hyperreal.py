"""Regenerate image with hyper-realistic prompts"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.fal_seedream_service import FalSeedreamService

async def regenerate():
    service = FalSeedreamService("starbright_monroe")
    
    result = await service.transform_with_pose_source(
        pose_source_path="content/transform_input/012426transform_5/12426 transform 5/SnapInsta.to_612397752_17907539271300901_6671042915091524151_n.jpg",
        pose_description="mirror selfie, one arm raised up touching hair/head, other hand holding pink phone, standing facing mirror",
        outfit_description="leopard print bodysuit with thin straps, silver bracelets",
        background_description="modern bathroom/closet with gold shelf, perfume bottles visible",
        filename_prefix="hyperreal_612397752"
    )
    
    if result.get("status") == "success":
        print(f"SUCCESS: {result['image_path']}")
    else:
        print(f"FAILED: {result.get('error', 'Unknown')}")

print("Regenerating with hyper-realistic prompts...")
asyncio.run(regenerate())
