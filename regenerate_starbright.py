"""Quick regeneration with adjusted parameters for better body proportions"""
import asyncio
import os
import sys
sys.path.insert(0, '.')

from app.services.fal_seedream_service import FalSeedreamService

async def regenerate():
    service = FalSeedreamService(influencer_id="starbright_monroe")
    
    # Build prompt with realistic background and accurate body
    prompt = service.build_prompt(
        scene="modern minimalist bedroom interior, properly scaled furniture, realistic perspective, camera at eye level",
        outfit="red crop top and red shorts matching set",
        pose="standing naturally with relaxed confident pose, full body visible, feet on ground",
        lighting="soft natural daylight from window, realistic shadows",
        additional="extremely thin slender petite body, very small A-cup chest, flat chest appearance, slim narrow frame, proportionate to environment"
    )
    
    # Strong negative prompt for bust size and perspective issues
    negative_prompt = (
        "large breasts, big breasts, exaggerated chest, prominent bust, amplified cleavage, "
        "unrealistic body proportions, enhanced chest, busty, voluptuous, curvy chest, "
        "oversized furniture, wrong perspective, floating, wrong scale, disproportionate background, "
        "distorted perspective, unrealistic room size"
    )
    
    print(f"Prompt: {prompt[:200]}...")
    print(f"Negative: {negative_prompt[:100]}...")
    
    result = await service.generate_with_references(
        prompt=prompt,
        aspect_ratio="portrait_4_3",
        output_dir="content/generated/starbright_monroe",
        filename_prefix="starbright_monroe",
        enable_safety_checker=False,
        negative_prompt=negative_prompt
    )
    
    if result.get("status") == "success":
        print(f"\nSuccess! Image saved to: {result.get('saved_path')}")
    else:
        print(f"\nError: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    asyncio.run(regenerate())
