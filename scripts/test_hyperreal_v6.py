import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.seedream4_service import Seedream4Service

async def main():
    service = Seedream4Service()
    
    face_ref = "content/references/starbright_monroe/starbright_face_reference_v3.png"
    body_ref = "content/references/starbright_monroe/body_reference_blue_upscaled.png"
    source_image = "content/sources/starbright_monroe/hellokitty_bikini_source.jpg"
    
    identity = (
        "extremely pale porcelain ivory white cool-toned skin with visible pores and subtle skin imperfections, "
        "straight sleek dark brown hair past shoulders with natural flyaway strands, "
        "distinctive warm olive-brown hazel eyes with natural catchlight reflections, "
        "prominent visible natural freckles scattered across nose bridge and upper cheeks, "
        "very petite slim boyish straight figure like a young ballet dancer with no prominent curves, "
        "thin delicate frame"
    )
    
    prompt = (
        f"Figure 1 face identity, Figure 2 body proportions, Figure 3 exact pose and outfit. "
        f"Raw unedited photograph of a real 19-year-old woman with {identity}, "
        f"bare ears with absolutely no earrings no jewelry, "
        f"wearing the exact same Hello Kitty bikini outfit as Figure 3 with cat ear headband, "
        f"standing in a bright minimalist white bedroom, sheer curtains with soft natural daylight, white bedding behind, "
        f"cool overcast natural window light. "
        f"RAW photo, unretouched, real human skin with visible pores and micro-texture, "
        f"slight under-eye shadows, natural lip color variation, asymmetric facial features, "
        f"real hair strands not rendered, subsurface scattering on ear edges, "
        f"shot on Sony A7IV, Sigma 85mm f/1.4 Art lens wide open, shallow depth of field, "
        f"natural bokeh, ISO 400, slight film grain, color graded like editorial fashion photography"
    )
    
    print("Generating hyper-real V6...")
    
    result = await service.transform_image(
        source_image_path=source_image,
        prompt=prompt,
        aspect_ratio="3:4",
        filename_prefix="hellokitty_hyperreal_v6",
        size="4K",
        body_ref=body_ref,
        face_ref=face_ref
    )
    
    if result and result.get("status") == "success":
        print(f"SUCCESS: {result.get('output_path', result.get('image_path'))}")
    else:
        print(f"RESULT: {result}")

if __name__ == "__main__":
    asyncio.run(main())
