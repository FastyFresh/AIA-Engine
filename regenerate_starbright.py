"""Generate 4 variations in luxury bedroom - no clothing"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.fal_seedream_service import FalSeedreamService

async def regenerate():
    service = FalSeedreamService(influencer_id="starbright_monroe")
    
    poses = [
        "standing naturally with relaxed pose, hand on hip, full body visible",
        "standing confidently with arms relaxed at sides, full body visible", 
        "standing with slight lean, relaxed natural pose, full body visible",
        "standing casually, natural confident pose, full body visible"
    ]
    
    results = []
    for i, pose in enumerate(poses):
        print(f"\n--- Generating variation {i+1}/4 ---")
        prompt = service.build_prompt(
            scene="spacious bright modern luxury penthouse bedroom, floor to ceiling windows with natural sunlight flooding in, high double-height ceilings, designer furniture, clothes scattered on floor, personal items on nightstand, lived-in feel, king size bed with rumpled white sheets",
            outfit="",
            pose=pose,
            lighting="bright natural daylight flooding through large windows, warm golden hour sunlit atmosphere",
            additional="slim healthy petite body matching body reference exactly, natural healthy proportions, small A-cup chest"
        )
        
        result = await service.generate_with_references(
            prompt=prompt,
            aspect_ratio="portrait_4_3",
            output_dir="content/generated/starbright_monroe",
            filename_prefix="starbright_monroe",
            enable_safety_checker=False
        )
        
        status = result.get("status", "error")
        print(f"Variation {i+1}: {status}")
        results.append(result)
    
    print("\nDone generating 4 variations!")
    return results

if __name__ == "__main__":
    asyncio.run(regenerate())
