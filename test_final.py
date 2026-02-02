"""Test with different background"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.fal_seedream_service import FalSeedreamService

async def test():
    service = FalSeedreamService("starbright_monroe")
    
    # Test with living room background
    result = await service.transform_with_pose_source(
        pose_source_path="content/transform_input/012426transform_5/12426 transform 5/SnapInsta.to_618243808_17870044350521702_913157187533577010_n.jpg",
        pose_description="sitting on bed, both hands behind head touching hair, looking at camera with soft expression, knees bent",
        outfit_description="floral print string bikini with colorful pattern, small heart necklace",
        background_description="modern luxury living room with designer furniture",
        background_ref_path="content/references/backgrounds/modern_luxury_living_room.png",
        filename_prefix="test_livingroom"
    )
    
    if result.get("status") == "success":
        print(f"SUCCESS: {result['image_path']}")
    else:
        print(f"FAILED: {result.get('error', 'Unknown')}")

print("Testing with living room background...")
asyncio.run(test())
