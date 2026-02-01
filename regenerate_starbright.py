"""Generate multiple test images with varied lived-in scenes"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.fal_seedream_service import FalSeedreamService

async def regenerate():
    service = FalSeedreamService(influencer_id="starbright_monroe")
    
    scenes = [
        {
            "scene": "small cozy apartment living room, clothes tossed on couch, coffee mug on table, magazines scattered, shoes kicked off near door, compact space scaled to petite person",
            "outfit": "casual oversized sweater and shorts",
            "pose": "standing casually leaning against wall, full body visible"
        },
        {
            "scene": "intimate bedroom with unmade bed, clothes on floor, phone charger on nightstand, small vanity with makeup, cozy proportioned room matching petite frame",
            "outfit": "white tank top and grey sweatpants",
            "pose": "standing relaxed with arms at sides, full body grounded"
        },
        {
            "scene": "bathroom doorway, towels hanging, skincare products on counter, robe on hook, small personal bathroom scale appropriate to slim petite person",
            "outfit": "light blue athletic set",
            "pose": "natural standing pose, full body visible, feet on floor"
        }
    ]
    
    results = []
    for i, s in enumerate(scenes):
        print(f"\n--- Generating scene {i+1}/3 ---")
        prompt = service.build_prompt(
            scene=s["scene"],
            outfit=s["outfit"],
            pose=s["pose"],
            lighting="soft natural daylight, realistic shadows",
            additional="extremely thin slender petite body, very small flat A-cup chest, slim narrow frame"
        )
        
        result = await service.generate_with_references(
            prompt=prompt,
            aspect_ratio="portrait_4_3",
            output_dir="content/generated/starbright_monroe",
            filename_prefix="starbright_monroe",
            enable_safety_checker=False
        )
        
        status = result.get("status", "error")
        print(f"Scene {i+1}: {status}")
        results.append(result)
    
    print("\nDone generating 3 test images!")
    return results

if __name__ == "__main__":
    asyncio.run(regenerate())
