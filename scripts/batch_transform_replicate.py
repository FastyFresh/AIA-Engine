"""
Batch Transform Images to Starbright Monroe using Replicate Seedream 4.5

Processes images in batches of 2 at a time, transforming them into Starbright Monroe
while preserving pose, scene, and composition from the source images.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.seedream4_service import Seedream4Service
from app.services.prompt_builder import PromptBuilder

SOURCE_DIR = "attached_assets/transform_batch/012426transform 4"
BATCH_SIZE = 2

TRANSFORM_PROMPT_TEMPLATE = """
Figure 1 is a young woman with very pale porcelain ivory white skin, straight sleek dark brown hair (not wavy, not curly), 
warm olive-brown eyes, natural freckles across nose and cheeks, 
extremely thin slender petite body with very narrow tiny waist, 
slim narrow hips, long thin slender legs, delicate small frame, size 0 figure,
small natural A-cup breasts, proportionate feminine figure.

Transform Figure 3 (the reference pose image) into Figure 1's appearance while maintaining the exact same pose, 
camera angle, scene, lighting, and composition from Figure 3.

natural skin texture with visible pores, fine skin detail, 
slight natural skin imperfections, photorealistic skin tones, 
no plastic skin, no airbrushed, no over-smoothed, no beauty filter,
Shot on Canon EOS R5, 85mm f/1.4 lens, 8K ultra detailed, cinematic lighting
"""


async def transform_batch(service: Seedream4Service, image_paths: list, batch_num: int):
    """Process a batch of images"""
    results = []
    
    for i, image_path in enumerate(image_paths):
        img_name = Path(image_path).stem
        short_name = img_name[:20] if len(img_name) > 20 else img_name
        prefix = f"starbright_transform_{batch_num}_{i+1}"
        
        print(f"  Transforming: {short_name}...")
        
        result = await service.transform_image(
            source_image_path=image_path,
            prompt=TRANSFORM_PROMPT_TEMPLATE,
            aspect_ratio="3:4",
            filename_prefix=prefix,
            size="4K"
        )
        
        if result["status"] == "success":
            print(f"    SUCCESS: {result['filename']}")
        else:
            print(f"    FAILED: {result.get('error', 'Unknown error')}")
        
        results.append({
            "source": image_path,
            "result": result
        })
    
    return results


async def main():
    print("=" * 60)
    print("Batch Transform to Starbright Monroe (Replicate Seedream 4.5)")
    print("=" * 60)
    
    source_dir = Path(SOURCE_DIR)
    if not source_dir.exists():
        print(f"ERROR: Source directory not found: {SOURCE_DIR}")
        return
    
    images = sorted([
        str(f) for f in source_dir.glob("*.jpg")
        if not f.name.startswith("._")
    ])
    
    print(f"\nFound {len(images)} images to transform")
    print(f"Processing in batches of {BATCH_SIZE}")
    print("-" * 60)
    
    service = Seedream4Service(influencer_id="starbright_monroe")
    
    all_results = []
    num_batches = (len(images) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_idx in range(num_batches):
        start_idx = batch_idx * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(images))
        batch_images = images[start_idx:end_idx]
        
        print(f"\n[Batch {batch_idx + 1}/{num_batches}] Processing {len(batch_images)} images...")
        
        batch_results = await transform_batch(service, batch_images, batch_idx + 1)
        all_results.extend(batch_results)
        
        if batch_idx < num_batches - 1:
            print(f"  Pausing before next batch...")
            await asyncio.sleep(2)
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    
    successes = [r for r in all_results if r["result"]["status"] == "success"]
    failures = [r for r in all_results if r["result"]["status"] != "success"]
    
    print(f"\nSuccessful: {len(successes)}/{len(all_results)}")
    print(f"Failed: {len(failures)}/{len(all_results)}")
    
    if successes:
        print("\nGenerated images saved to: content/seedream4_output/")
        for r in successes:
            print(f"  - {r['result']['filename']}")
    
    if failures:
        print("\nFailed transformations:")
        for r in failures:
            src_name = Path(r["source"]).stem[:30]
            print(f"  - {src_name}: {r['result'].get('error', 'Unknown')}")


if __name__ == "__main__":
    asyncio.run(main())
