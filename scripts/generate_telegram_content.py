"""
Generate Telegram content for both Luna Vale and Starbright Monroe
with matching poses, outfits, and backgrounds.
"""
import asyncio
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.seedream4_service import Seedream4Service


CONTENT_SPECS = {
    "welcome_pack": [
        {
            "outfit": "casual white cropped tank top with high-waisted denim shorts",
            "scene": "modern minimalist apartment with floor-to-ceiling windows, morning sunlight",
            "pose": "relaxed seated pose on modern couch, one leg tucked under",
            "lighting": "soft morning sunlight streaming through windows, warm golden hour glow"
        },
        {
            "outfit": "oversized cream knit sweater with black leggings",
            "scene": "cozy bedroom with neutral bedding, plants on windowsill",
            "pose": "standing by window looking out, contemplative natural pose",
            "lighting": "soft diffused natural light, intimate atmosphere"
        },
        {
            "outfit": "elegant black slip dress with thin straps",
            "scene": "upscale rooftop terrace at sunset, city skyline in background",
            "pose": "leaning against railing, looking over shoulder at camera",
            "lighting": "golden hour sunset lighting, warm and romantic"
        }
    ],
    "teaser": [
        {
            "outfit": "elegant off-shoulder white sweater with delicate neckline",
            "scene": "luxurious hotel room with crisp white bedding, soft textures",
            "pose": "sitting on edge of bed, playful confident expression",
            "lighting": "soft window light creating gentle shadows"
        },
        {
            "outfit": "silk robe loosely tied, elegant and tasteful",
            "scene": "marble bathroom vanity with soft lighting, mirror reflection",
            "pose": "applying lipstick in mirror, getting ready",
            "lighting": "warm vanity lighting, soft and flattering"
        },
        {
            "outfit": "fitted workout set, sports bra and high-waisted leggings",
            "scene": "modern home gym with floor-to-ceiling windows",
            "pose": "mid-stretch, athletic and confident",
            "lighting": "bright natural daylight, energetic atmosphere"
        }
    ],
    "companion": [
        {
            "outfit": "elegant emerald green cocktail dress, sophisticated cut",
            "scene": "upscale restaurant with dim ambient lighting, candlelit table",
            "pose": "seated at table, chin resting on hand, engaged expression",
            "lighting": "warm candlelight with soft ambient glow"
        },
        {
            "outfit": "cozy cashmere sweater dress in dusty rose",
            "scene": "bookstore cafe corner with vintage decor, coffee cup nearby",
            "pose": "curled up in armchair reading, peaceful expression",
            "lighting": "warm indoor lighting, cozy atmosphere"
        },
        {
            "outfit": "tailored blazer over simple white tee, smart casual",
            "scene": "modern art gallery, minimalist white walls, abstract art",
            "pose": "contemplating artwork, profile view",
            "lighting": "soft gallery lighting, clean and modern"
        }
    ],
    "vip": [
        {
            "outfit": "elegant black satin evening gown with low back",
            "scene": "luxurious penthouse living room, floor-to-ceiling city views at night",
            "pose": "standing by window, confident sophisticated gaze",
            "lighting": "soft ambient city lights, intimate atmosphere"
        },
        {
            "outfit": "elegant champagne-colored silk maxi dress, refined",
            "scene": "private yacht deck at sunset, ocean horizon",
            "pose": "lounging on deck furniture, wind in hair",
            "lighting": "golden sunset glow, warm and dreamy"
        },
        {
            "outfit": "luxurious white silk robe with satin trim, tasteful",
            "scene": "boutique hotel suite with French windows, morning light",
            "pose": "standing by curtains, soft natural pose",
            "lighting": "soft morning light through sheer curtains"
        }
    ]
}


async def generate_for_persona(persona: str, content_type: str, specs: list):
    """Generate images for a specific persona and content type."""
    service = Seedream4Service(influencer_id=persona)
    results = []
    
    output_dir = Path(f"content/telegram/{persona.replace('_monroe', '').replace('_vale', '')}/{content_type}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    gallery_dir = Path(f"content/generated/{persona}")
    gallery_dir.mkdir(parents=True, exist_ok=True)
    
    for i, spec in enumerate(specs):
        print(f"\n[{persona}] Generating {content_type} image {i+1}/{len(specs)}...")
        
        prompt = service.build_prompt(
            scene=spec["scene"],
            outfit=spec["outfit"],
            pose=spec["pose"],
            lighting=spec["lighting"],
            accessories="minimal"
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{persona.split('_')[0]}_{content_type}"
        
        result = await service.generate(
            prompt=prompt,
            aspect_ratio="9:16",
            filename_prefix=prefix
        )
        
        if result.get("status") == "success":
            src_path = result.get("image_path")
            if src_path and Path(src_path).exists():
                new_filename = f"{prefix}_{timestamp}_{i+1}.png"
                dest_path = output_dir / new_filename
                shutil.copy(src_path, dest_path)
                
                gallery_path = gallery_dir / new_filename
                shutil.copy(src_path, gallery_path)
                
                results.append({
                    "status": "success",
                    "telegram_path": str(dest_path),
                    "gallery_path": str(gallery_path)
                })
                print(f"  ✓ Saved to {dest_path}")
            else:
                results.append({"status": "error", "error": "No image path returned"})
                print(f"  ✗ Error: No image path")
        else:
            results.append(result)
            print(f"  ✗ Error: {result.get('error', 'Unknown')}")
        
        await asyncio.sleep(2)
    
    return results


async def main():
    """Generate all content for both personas."""
    
    personas = ["luna_vale", "starbright_monroe"]
    content_types = ["welcome_pack", "teaser", "companion", "vip"]
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--persona", choices=personas + ["both"], default="both")
    parser.add_argument("--type", choices=content_types + ["all"], default="all")
    args = parser.parse_args()
    
    if args.persona == "both":
        selected_personas = personas
    else:
        selected_personas = [args.persona]
    
    if args.type == "all":
        selected_types = content_types
    else:
        selected_types = [args.type]
    
    print("=" * 60)
    print("Telegram Content Generator")
    print("=" * 60)
    print(f"Personas: {', '.join(selected_personas)}")
    print(f"Content types: {', '.join(selected_types)}")
    print("=" * 60)
    
    all_results = {}
    
    for persona in selected_personas:
        print(f"\n{'='*60}")
        print(f"GENERATING FOR: {persona.upper()}")
        print(f"{'='*60}")
        
        all_results[persona] = {}
        
        for content_type in selected_types:
            if content_type in CONTENT_SPECS:
                specs = CONTENT_SPECS[content_type]
                print(f"\n--- {content_type.upper()} ({len(specs)} images) ---")
                results = await generate_for_persona(persona, content_type, specs)
                all_results[persona][content_type] = results
    
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    
    for persona, types in all_results.items():
        print(f"\n{persona}:")
        for content_type, results in types.items():
            success = sum(1 for r in results if r.get("status") == "success")
            print(f"  {content_type}: {success}/{len(results)} successful")
    
    return all_results


if __name__ == "__main__":
    asyncio.run(main())
