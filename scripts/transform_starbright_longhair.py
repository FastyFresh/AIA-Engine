"""
SEEDream 4.5 Enhanced 5-Reference Transformation - Long Hair Variations
Uses Starbright's longer hair from face references instead of source image's shorter hair.
Generates 3 variations.
"""

import os
import base64
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

FAL_SEEDREAM_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

POSE_SOURCE = "attached_assets/SnapInsta.to_608765981_17891349522393680_9103223354686423306_n_1770338654748.jpg"
FACE_REF_1 = "content/references/starbright_monroe/starbright_face_reference_v3.webp"
FACE_REF_2 = "content/references/starbright_monroe/canonical_face/starbright_face_canonical.png"
BODY_REF_1 = "content/references/starbright_monroe/body_reference_goal.webp"
BODY_REF_2 = "content/references/starbright_monroe/body_reference_ivory.webp"

OUTPUT_DIR = "content/seedream4_output"

NEGATIVE_PROMPT = "cartoon, anime, illustration, painting, blue eyes, grey eyes, green eyes, short hair, bob haircut, pixie cut, shoulder-length hair, extra limbs, extra fingers, deformed, blurry skin, plastic skin, airbrushed, overly smooth skin, mannequin, tan skin, dark skin, different face, wrong face, different person, muscular, thick thighs, wide hips, large breasts, extra arms, extra legs, mutated hands, fused fingers, too many fingers, missing fingers, bad anatomy, different pose, wrong pose, different angle, wrong camera angle, multiple people, two people"

PROMPTS = [
    {
        "prefix": "starbright_longhair_v1",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND hairstyle (long straight dark brown hair).
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

POSE (COPY EXACTLY FROM IMAGE 1):
Standing upright with body slightly angled to the left, right arm extended up and to the right gripping onto white sheer curtain fabric at head height, left hand resting near left hip with fingers slightly extended and curled, head tilted slightly to the right with a warm smile, shoulders relaxed and slightly back, weight distributed on both legs with subtle hip shift to the left, camera angle straight on at chest level, full body visible from head to upper thighs.

OUTFIT (FROM IMAGE 1): Red floral lace crop top with thin spaghetti straps and matching red floral lace tie-side bottoms with red ribbon ties on both hips.
HAIRSTYLE (FROM IMAGE 2 AND IMAGE 3): Very long straight sleek dark brown hair flowing down past shoulders, smooth and straight, reaching mid-chest length. Use the long hair from the face references, NOT the short hair from Image 1.
BACKGROUND: from Image 1 - bright indoor setting with white sheer curtains on both sides, soft diffused natural daylight flooding in, clean bright backdrop.

FACE (from Image 2 and Image 3 ONLY):
  * Olive-brown warm eyes with exact eye shape
  * Very pale porcelain ivory white skin tone
  * Natural freckles scattered across nose and cheeks
  * Exact nose shape, lip shape, and jawline from references
  * Natural skin texture with visible pores
  * Warm confident smile

BODY (from Image 4 and Image 5 ONLY):
  * Extremely thin slender frame with very narrow tiny waist
  * Slim narrow hips with long thin slender legs
  * Small natural A-cup breasts
  * Very pale porcelain ivory white skin tone

Shot on Canon EOS R5, 85mm f/1.4 lens, natural skin texture with visible pores, 8K ultra detailed, photorealistic.

ABSOLUTE RULES:
1. POSE from Image 1 exactly
2. CAMERA ANGLE identical to Image 1
3. LONG HAIR from Image 2 and Image 3 (NOT Image 1's short hair)
4. Face identity from Image 2 and Image 3 ONLY
5. Body proportions from Image 4 and Image 5 ONLY"""
    },
    {
        "prefix": "starbright_longhair_v2",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND hairstyle (long dark brown hair flowing past shoulders).
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

POSE (COPY EXACTLY FROM IMAGE 1):
Standing upright with body slightly angled to the left, right arm raised up and to the right holding onto white sheer curtain at head height, left hand positioned near left hip with fingers slightly spread, head tilted gently to the right with a confident smile showing teeth, shoulders relaxed, weight on both legs with a subtle leftward hip shift, camera straight on at chest level, framing from head to upper thighs.

OUTFIT (FROM IMAGE 1): Red floral lace crop top with thin spaghetti straps and matching red floral lace tie-side bottoms with red ribbon ties on both hips.
HAIRSTYLE: Very long straight sleek dark brown hair from Image 2 and Image 3, flowing down well past the shoulders, smooth and straight with subtle shine. DO NOT use Image 1's short wavy hair.
BACKGROUND: Bright indoor setting with white sheer curtains, soft natural daylight, clean and airy.

FACE (from Image 2 and Image 3 ONLY):
  * Olive-brown warm eyes
  * Very pale porcelain ivory white skin
  * Natural freckles across nose and cheeks
  * Delicate features, full lips with cupid's bow
  * Natural skin texture, visible pores
  * Smiling warmly at camera

BODY (from Image 4 and Image 5 ONLY):
  * Extremely thin slender petite frame
  * Very narrow tiny waist, slim narrow hips
  * Long thin slender legs
  * Small natural A-cup breasts
  * Very pale porcelain ivory skin tone

Photorealistic photograph, shot on Canon EOS R5, 85mm f/1.4, natural skin detail with pores, 8K quality.

ABSOLUTE RULES:
1. POSE from Image 1 exactly
2. CAMERA ANGLE identical to Image 1
3. LONG straight dark brown hair from Image 2 and Image 3 ONLY
4. Face identity from Image 2 and Image 3 ONLY
5. Body proportions from Image 4 and Image 5 ONLY"""
    },
    {
        "prefix": "starbright_longhair_v3",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND long dark brown hairstyle.
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

POSE (COPY EXACTLY FROM IMAGE 1):
Standing upright, body angled slightly left, right arm extended upward gripping white curtain fabric, left hand near left hip area with relaxed fingers, head tilted slightly right, warm confident smile, shoulders back, weight on both feet with subtle hip shift left, straight-on camera angle at chest height, full body framing head to upper thighs.

OUTFIT (FROM IMAGE 1): Red floral lace crop top with thin straps and matching red floral lace tie-side bottoms with ribbon ties at both hips.
HAIRSTYLE (CRITICAL - FROM IMAGE 2 AND 3, NOT IMAGE 1): Long straight dark brown hair flowing past shoulders and draping over chest, sleek and smooth, dark chocolate brown color. The hair MUST be long as shown in Image 2 and Image 3. Absolutely do NOT use the short bob hair from Image 1.
BACKGROUND: Bright airy indoor setting, white sheer curtains draped on both sides, warm soft diffused natural daylight, clean minimalist backdrop.

FACE (from Image 2 and Image 3 ONLY):
  * Olive-brown warm eyes with almond shape
  * Very pale porcelain ivory white skin tone
  * Natural freckles scattered across nose and cheeks
  * Soft oval jaw, high cheekbones
  * Full natural lips
  * Natural skin with visible pores and texture
  * Confident warm expression

BODY (from Image 4 and Image 5 ONLY):
  * Extremely thin slender petite frame
  * Very narrow tiny waist
  * Slim narrow hips, long thin slender legs
  * Small natural A-cup breasts
  * Very pale porcelain ivory white skin

Shot on Canon EOS R5, 85mm f/1.4, 8K ultra detailed, photorealistic, natural lighting.

ABSOLUTE RULES:
1. POSE from Image 1 exactly
2. CAMERA ANGLE identical to Image 1
3. LONG dark brown hair from Image 2 and Image 3 (NOT Image 1)
4. Face identity from Image 2 and Image 3 ONLY
5. Body proportions from Image 4 and Image 5 ONLY"""
    }
]


def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/png")
    return f"data:{mime};base64,{data}"


async def transform_single(client, headers, prompt_config, image_urls):
    prefix = prompt_config["prefix"]
    prompt = prompt_config["prompt"]

    payload = {
        "prompt": prompt,
        "image_urls": image_urls,
        "image_size": {"width": 1080, "height": 1350},
        "num_images": 1,
        "max_images": 1,
        "guidance_scale": 7.0,
        "enable_safety_checker": False,
        "negative_prompt": NEGATIVE_PROMPT
    }

    print(f"\n[{prefix}] Sending request...")

    try:
        response = await client.post(
            FAL_SEEDREAM_URL,
            headers=headers,
            json=payload
        )

        print(f"[{prefix}] Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])

            if images:
                img_url = images[0].get("url", "")
                if img_url:
                    img_resp = await client.get(img_url)
                    if img_resp.status_code == 200:
                        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{prefix}_{timestamp}.png"
                        filepath = Path(OUTPUT_DIR) / filename
                        filepath.write_bytes(img_resp.content)

                        print(f"[{prefix}] SUCCESS! Saved: {filepath}")
                        return str(filepath)

            print(f"[{prefix}] No images in response")
            return None
        else:
            print(f"[{prefix}] API error {response.status_code}: {response.text[:500]}")
            return None

    except Exception as e:
        print(f"[{prefix}] ERROR: {str(e)}")
        return None


async def transform_all():
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not configured")
        return

    for p in [POSE_SOURCE, FACE_REF_1, FACE_REF_2, BODY_REF_1, BODY_REF_2]:
        if not Path(p).exists():
            print(f"ERROR: Missing file: {p}")
            return

    print("Encoding 5 reference images...")
    image_urls = [
        encode_image(POSE_SOURCE),
        encode_image(FACE_REF_1),
        encode_image(FACE_REF_2),
        encode_image(BODY_REF_1),
        encode_image(BODY_REF_2),
    ]

    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }

    print("=" * 60)
    print("SEEDream 4.5 - Long Hair Variations (3 images)")
    print("Hair: Long straight dark brown from face references")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=300.0) as client:
        tasks = [transform_single(client, headers, p, image_urls) for p in PROMPTS]
        results = await asyncio.gather(*tasks)

    print("\n" + "=" * 60)
    print("RESULTS:")
    for i, r in enumerate(results, 1):
        status = f"OK -> {r}" if r else "FAILED"
        print(f"  Variation {i}: {status}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(transform_all())
