"""Test replicating the exact kreator_precise_pose generation"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.fal_seedream_service import FalSeedreamService

async def test():
    service = FalSeedreamService("starbright_monroe")
    
    # Use the SAME source image as kreator_precise_pose
    result = await service.transform_with_pose_source(
        pose_source_path="content/transform_input/012426transform 4/SnapInsta.to_603828247_17866939128519906_3556279129994261783_n.jpg",
        pose_description="woman leaning forward with torso bent, hands resting on thighs near knees, head tilted slightly looking up at camera",
        outfit_description="white bralette and red shorts with white stripe",
        background_description="indoor room",
        filename_prefix="replicate_kreator"
    )
    
    if result.get("status") == "success":
        print(f"SUCCESS: {result['image_path']}")
    else:
        print(f"FAILED: {result.get('error', 'Unknown')}")

print("Testing to replicate kreator_precise_pose quality...")
asyncio.run(test())
