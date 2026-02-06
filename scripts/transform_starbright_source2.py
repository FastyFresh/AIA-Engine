"""
SEEDream 4.5 Enhanced 5-Reference Transformation - Source Image 2
Black t-shirt dress, couch pose, dark curtain background.
Uses Starbright's longer hair from face references.
Generates 3 variations.
"""

import os
import base64
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

FAL_SEEDREAM_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

POSE_SOURCE = "attached_assets/SnapInsta.to_614905900_17869977735531149_1109730748104460533_n_1770341051244.jpg"
FACE_REF_1 = "content/references/starbright_monroe/starbright_face_reference_v3.webp"
FACE_REF_2 = "content/references/starbright_monroe/canonical_face/starbright_face_canonical.png"
BODY_REF_1 = "content/references/starbright_monroe/body_reference_goal.webp"
BODY_REF_2 = "content/references/starbright_monroe/body_reference_ivory.webp"

OUTPUT_DIR = "content/seedream4_output"

NEGATIVE_PROMPT = "cartoon, anime, illustration, painting, blue eyes, grey eyes, green eyes, black hair, jet black hair, ponytail, hair tie, short hair, bob haircut, pixie cut, extra limbs, extra fingers, deformed, blurry skin, plastic skin, airbrushed, overly smooth skin, mannequin, tan skin, dark skin, different face, wrong face, different person, muscular, thick thighs, wide hips, large breasts, extra arms, extra legs, mutated hands, fused fingers, too many fingers, missing fingers, bad anatomy, different pose, wrong pose, different angle, wrong camera angle, multiple people, two people"

PROMPTS = [
    {
        "prefix": "starbright_src2_v1",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND hairstyle (long straight dark brown hair).
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

POSE (COPY EXACTLY FROM IMAGE 1):
Reclining casually on a cream-colored couch, leaning back to the right with upper body propped against the couch backrest, legs bent with knees raised toward camera, left leg crossed slightly over right leg, right arm extended behind along the couch, left arm resting in lap, head tilted slightly to the left with a neutral direct gaze at camera, slightly elevated camera angle looking down at the subject, close-up framing from upper thighs to above head.

OUTFIT (FROM IMAGE 1): Plain black oversized t-shirt dress or long t-shirt bunched at the waist, black athletic socks with three white stripes near the top on both feet.
HAIRSTYLE (FROM IMAGE 2 AND IMAGE 3): Very long straight sleek dark brown hair, flowing down past shoulders, smooth and straight. Use the long dark brown hair from the face references. DO NOT use Image 1's black ponytail hairstyle.
BACKGROUND: from Image 1 - dark black curtains behind the couch, cream/beige colored leather or fabric couch, dim moody indoor lighting with some natural light coming from the right side.

FACE (from Image 2 and Image 3 ONLY):
  * Olive-brown warm eyes with exact eye shape
  * Very pale porcelain ivory white skin tone
  * Natural freckles scattered across nose and cheeks
  * Exact nose shape, lip shape, and jawline from references
  * Natural skin texture with visible pores
  * Neutral confident expression with direct gaze, lips slightly parted

BODY (from Image 4 and Image 5 ONLY):
  * Extremely thin slender frame with very narrow tiny waist
  * Slim narrow hips with long thin slender legs
  * Small natural A-cup breasts
  * Very pale porcelain ivory white skin tone

Shot on Canon EOS R5, 35mm f/1.4 lens, natural skin texture with visible pores, 8K ultra detailed, photorealistic, moody lighting.

ABSOLUTE RULES:
1. POSE from Image 1 exactly - reclining on couch
2. CAMERA ANGLE identical to Image 1 - slightly elevated looking down
3. LONG dark brown hair from Image 2 and Image 3 (NOT Image 1's black ponytail)
4. Face identity from Image 2 and Image 3 ONLY
5. Body proportions from Image 4 and Image 5 ONLY"""
    },
    {
        "prefix": "starbright_src2_v2",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND hairstyle (long dark brown hair flowing past shoulders).
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

POSE (COPY EXACTLY FROM IMAGE 1):
Reclining on a cream-colored couch, leaning back and to the right against the backrest, legs drawn up with knees pointing toward the camera, left leg crossing slightly over right, right arm stretched back along the top of the couch, left arm resting loosely in the lap area, head tilted gently left with a calm neutral expression looking directly at camera, camera positioned slightly above subject looking downward, framing captures from upper thighs to above head.

OUTFIT (FROM IMAGE 1): Black oversized t-shirt dress bunched up around the waist, black crew socks with three white horizontal stripes on both feet.
HAIRSTYLE: Long straight dark brown hair from Image 2 and Image 3, flowing past the shoulders, smooth sleek straight hair draping naturally. DO NOT use the black ponytail from Image 1.
BACKGROUND: Dark black curtains behind, cream-beige couch, moody dim indoor setting with warm light entering from the right.

FACE (from Image 2 and Image 3 ONLY):
  * Olive-brown warm eyes
  * Very pale porcelain ivory white skin
  * Natural freckles across nose and cheeks
  * Soft features, natural lips slightly parted
  * Natural skin texture, visible pores
  * Direct neutral gaze at camera

BODY (from Image 4 and Image 5 ONLY):
  * Extremely thin slender petite frame
  * Very narrow tiny waist, slim narrow hips
  * Long thin slender legs
  * Small natural A-cup breasts
  * Very pale porcelain ivory white skin tone

Photorealistic, Canon EOS R5, 35mm f/1.4, natural skin detail, 8K quality, moody ambient lighting.

ABSOLUTE RULES:
1. POSE from Image 1 exactly - reclining on cream couch
2. CAMERA ANGLE identical to Image 1 - slightly above looking down
3. LONG straight dark brown hair from Image 2 and Image 3 ONLY
4. Face identity from Image 2 and Image 3 ONLY
5. Body proportions from Image 4 and Image 5 ONLY"""
    },
    {
        "prefix": "starbright_src2_v3",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND long dark brown hairstyle.
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

POSE (COPY EXACTLY FROM IMAGE 1):
Reclining casually on cream-colored couch, body leaned back to the right propped against backrest, both legs bent at the knees with knees raised toward the camera, left leg slightly crossing over right leg, right arm extended behind along couch back, left arm relaxed in lap, head tilted slightly left, looking directly at camera with neutral calm expression, camera angle slightly elevated above subject, close intimate framing from mid-thigh up to above head.

OUTFIT (FROM IMAGE 1): Plain black oversized t-shirt or t-shirt dress gathered at the waist, black crew socks with three white stripes on both feet.
HAIRSTYLE (CRITICAL - FROM IMAGE 2 AND 3, NOT IMAGE 1): Long straight dark brown hair flowing past shoulders, sleek smooth straight, dark chocolate brown color. The hair MUST be long as shown in Image 2 and Image 3. Absolutely do NOT use the black ponytail hair from Image 1.
BACKGROUND: Dark black curtains as backdrop, cream-beige leather couch, moody indoor setting with dim ambient light and natural light from right side, intimate cozy atmosphere.

FACE (from Image 2 and Image 3 ONLY):
  * Olive-brown warm eyes with almond shape
  * Very pale porcelain ivory white skin tone
  * Natural freckles scattered across nose and cheeks
  * Soft oval jaw, high cheekbones
  * Full natural lips, slightly parted
  * Natural skin with visible pores and texture
  * Calm direct neutral gaze

BODY (from Image 4 and Image 5 ONLY):
  * Extremely thin slender petite frame
  * Very narrow tiny waist
  * Slim narrow hips, long thin slender legs
  * Small natural A-cup breasts
  * Very pale porcelain ivory white skin

Shot on Canon EOS R5, 35mm f/1.4, 8K ultra detailed, photorealistic, moody natural lighting.

ABSOLUTE RULES:
1. POSE from Image 1 exactly - reclining on couch
2. CAMERA ANGLE identical to Image 1 - slightly elevated
3. LONG dark brown hair from Image 2 and Image 3 (NOT Image 1's black ponytail)
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
    print("SEEDream 4.5 - Source 2: Black T-shirt Couch Pose")
    print("Hair: Long straight dark brown from face references")
    print("3 variations")
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
