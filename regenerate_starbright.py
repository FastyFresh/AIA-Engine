"""Quick regeneration with lived-in background details"""
import asyncio
import os
import sys
sys.path.insert(0, '.')

from app.services.fal_seedream_service import FalSeedreamService

async def regenerate():
    service = FalSeedreamService(influencer_id="starbright_monroe")
    
    # Build prompt with lived-in background details
    prompt = service.build_prompt(
        scene="cozy lived-in bedroom, clothes scattered on floor, throw blanket draped on chair, shoes by the door, personal items on nightstand, slightly messy but stylish, real home environment",
        outfit="red crop top and red shorts matching set",
        pose="standing naturally with relaxed confident pose, full body visible, feet on ground",
        lighting="soft natural daylight from window, warm realistic lighting",
        additional="extremely thin slender petite body, very small A-cup chest, flat chest appearance, slim narrow frame"
    )
    
    print(f"Prompt: {prompt[:300]}...")
    
    result = await service.generate_with_references(
        prompt=prompt,
        aspect_ratio="portrait_4_3",
        output_dir="content/generated/starbright_monroe",
        filename_prefix="starbright_monroe",
        enable_safety_checker=False
    )
    
    if result.get("status") == "success":
        print(f"\nSuccess! Image saved to: {result.get('saved_path')}")
    else:
        print(f"\nError: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    asyncio.run(regenerate())
