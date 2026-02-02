"""Test fal.ai Seedream generation with face/body references"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.fal_seedream_service import FalSeedreamService

async def main():
    service = FalSeedreamService(influencer_id="starbright_monroe")
    
    prompt = service.build_prompt(
        scene="modern luxury bedroom with white platform bed, soft morning light",
        outfit="white bralette and red shorts",
        pose="leaning forward slightly, looking at camera",
        lighting="soft natural morning light",
        additional="slim healthy petite body, natural A-cup proportions"
    )
    
    print("Generated prompt:")
    print(prompt[:500])
    print("...")
    
    print("\nGenerating with fal.ai...")
    result = await service.generate_with_references(
        prompt=prompt,
        aspect_ratio="portrait_4_3",
        output_dir="content/generated/starbright_monroe",
        filename_prefix="fal_test",
        enable_safety_checker=False
    )
    
    print(f"Status: {result.get('status')}")
    if result.get('error'):
        print(f"Error: {result.get('error')}")
    if result.get('image_path'):
        print(f"Saved: {result.get('image_path')}")

asyncio.run(main())
