"""Batch transform images using Kreator Flow method"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.fal_seedream_service import FalSeedreamService

batch4 = [
    {
        "path": "content/transform_input/012426transform_5/12426 transform 5/SnapInsta.to_615400310_17945922006093613_5469120048892702247_n.jpg",
        "pose": "sitting on bathroom floor next to jacuzzi tub, wet hair falling over face, looking up at camera from low angle, one arm extended toward camera",
        "outfit": "pink bandeau/tube top bikini",
        "background": "luxury bathroom with white jacuzzi tub, gray tile floor, wet/spa setting",
        "prefix": "batch5_615400310"
    },
    {
        "path": "content/transform_input/012426transform_5/12426 transform 5/SnapInsta.to_615554787_18389529370148413_3275949796988668167_n.jpg",
        "pose": "kneeling on hardwood floor, one hand touching shoulder/chest, looking to the side with sultry expression, legs folded under",
        "outfit": "white satin corset with hook closures, white lace ruffled panties, nude thigh-high stockings with lace tops",
        "background": "room with cute floral wallpaper featuring roses and butterflies, dark hardwood floor with white baseboard",
        "prefix": "batch5_615554787"
    },
    {
        "path": "content/transform_input/012426transform_5/12426 transform 5/SnapInsta.to_616177128_17873311512489496_840722816201907119_n.jpg",
        "pose": "standing straight facing camera, arms relaxed at sides, slight smile, full body shot",
        "outfit": "light blue/periwinkle string bikini with triangle top and thong bottoms",
        "background": "bright living room with large windows showing outdoor view, cream sofa, modern minimalist decor",
        "prefix": "batch5_616177128"
    },
    {
        "path": "content/transform_input/012426transform_5/12426 transform 5/SnapInsta.to_618243808_17870044350521702_913157187533577010_n.jpg",
        "pose": "sitting on bed, both hands behind head touching hair, looking at camera with soft expression, knees bent",
        "outfit": "floral print string bikini with colorful pattern, small heart necklace",
        "background": "bright boho bedroom with white bedding, hanging plants, window with natural sunlight, wooden furniture",
        "prefix": "batch5_618243808"
    }
]

async def process_batch(images):
    service = FalSeedreamService("starbright_monroe")
    tasks = [
        service.transform_with_pose_source(
            pose_source_path=img["path"],
            pose_description=img["pose"],
            outfit_description=img["outfit"],
            background_description=img["background"],
            filename_prefix=img["prefix"]
        ) for img in images
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"[{i+1}] ERROR: {result}")
        elif result.get("status") == "success":
            print(f"[{i+1}] SUCCESS: {result['image_path']}")
        else:
            print(f"[{i+1}] FAILED: {result.get('error', 'Unknown')}")

print("Processing batch 4 (4 images concurrently)...")
asyncio.run(process_batch(batch4))
print("\nBatch 4 complete! All images processed.")
