"""Test with original working prompt structure"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.fal_seedream_service import FalSeedreamService

async def test():
    service = FalSeedreamService("starbright_monroe")
    
    result = await service.transform_with_pose_source(
        pose_source_path="content/transform_input/012426transform_5/12426 transform 5/SnapInsta.to_612435737_18035952221742596_8867320284577363603_n.jpg",
        pose_description="standing straight facing camera, hands resting on outer thighs, big smile, full body shot",
        outfit_description="teal/turquoise triangle bikini top with pink trim, hot pink high-cut bikini bottoms",
        background_description="luxury hotel suite with elegant decor",
        background_ref_path="content/references/backgrounds/luxury_hotel_suite.png",
        filename_prefix="original_prompt_test"
    )
    
    if result.get("status") == "success":
        print(f"SUCCESS: {result['image_path']}")
    else:
        print(f"FAILED: {result.get('error', 'Unknown')}")

print("Testing with original working prompt structure...")
asyncio.run(test())
