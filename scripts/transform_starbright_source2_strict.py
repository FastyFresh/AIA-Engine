"""
SEEDream 4.5 Enhanced 5-Reference - Source 2 STRICT POSE
Tighter pose description + higher guidance scale to reduce pose drift.
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

NEGATIVE_PROMPT = "cartoon, anime, illustration, painting, blue eyes, grey eyes, green eyes, black hair, jet black hair, ponytail, hair tie, short hair, bob haircut, pixie cut, sitting upright, standing, t-shirt, t-shirt dress, oversized shirt, loose shirt, extra limbs, extra fingers, deformed, blurry skin, plastic skin, airbrushed, overly smooth skin, mannequin, tan skin, dark skin, different face, wrong face, different person, muscular, thick thighs, wide hips, large breasts, extra arms, extra legs, mutated hands, fused fingers, too many fingers, missing fingers, bad anatomy, different pose, wrong pose, different angle, wrong camera angle, multiple people, two people"

PROMPTS = [
    {
        "prefix": "starbright_src2_strict_v1",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision. DO NOT deviate from Image 1's pose in any way.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND hairstyle (long straight dark brown hair).
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

POSE (COPY EXACTLY FROM IMAGE 1 - EXTREMELY STRICT):
Deep recline on cream couch - the subject is slumped far back into the couch at roughly a 45-degree recline angle, NOT sitting upright. Right arm is draped lazily backward along the top of the couch backrest behind her head. Left arm hangs down loosely at her left side resting on the couch seat. Head is tilted to the LEFT leaning against the couch back, chin slightly raised. LEGS ARE CRITICAL: Both knees are bent and raised HIGH, pointing almost directly at the camera. Left knee is slightly higher and crosses over the right leg. The knees and lower shins with striped socks dominate the lower foreground of the frame - they are VERY close to the camera lens. Feet with black striped socks are visible in the bottom of the frame very close to camera.

CAMERA ANGLE (CRITICAL): Shooting from slightly ABOVE and in front of the subject, looking DOWN at her reclined on the couch. This is NOT a straight-on shot - it is a selfie-style overhead angle. The perspective makes the knees appear large in the foreground due to wide-angle lens distortion.

FRAMING: Close intimate shot. Knees and socked feet fill the bottom third of the frame. Torso in the middle. Face in the upper portion tilted against the couch back. Dark curtains fill the background behind the couch.

OUTFIT (FROM IMAGE 1): Black fitted leotard bodysuit with short sleeves and a round neckline, form-fitting and snug against the body, black crew socks with three white horizontal stripes on both feet.
HAIRSTYLE (FROM IMAGE 2 AND IMAGE 3): Long straight dark brown hair flowing down past shoulders. DO NOT use Image 1's black ponytail.
BACKGROUND: Dark black curtains directly behind the cream/beige couch, dim moody lighting with some natural light from the right window.

FACE (from Image 2 and Image 3 ONLY):
  * Olive-brown warm eyes with exact eye shape
  * Very pale porcelain ivory white skin tone
  * Natural freckles scattered across nose and cheeks
  * Exact nose shape, lip shape, and jawline from references
  * Natural skin texture with visible pores
  * Neutral calm expression with direct gaze, lips slightly parted

BODY (from Image 4 and Image 5 ONLY):
  * Extremely thin slender frame with very narrow tiny waist
  * Slim narrow hips with long thin slender legs
  * Small natural A-cup breasts
  * Very pale porcelain ivory white skin tone

Shot on smartphone wide-angle selfie camera, natural skin texture, 8K ultra detailed, photorealistic, moody indoor lighting.

ABSOLUTE RULES:
1. DEEP RECLINE pose from Image 1 exactly - NOT sitting upright
2. OVERHEAD selfie camera angle from Image 1 - looking DOWN
3. KNEES CLOSE TO CAMERA filling bottom of frame exactly as Image 1
4. LONG dark brown hair from Image 2 and Image 3 (NOT Image 1's black ponytail)
5. Face identity from Image 2 and Image 3 ONLY
6. Body proportions from Image 4 and Image 5 ONLY"""
    },
    {
        "prefix": "starbright_src2_strict_v2",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision. The pose from Image 1 is PARAMOUNT.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND hairstyle (long dark brown hair).
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

POSE (REPLICATE IMAGE 1 EXACTLY - ZERO DEVIATION):
Subject is deeply reclined on a cream-colored couch, leaning far back at a steep angle with her back and head resting against the couch backrest. She is NOT sitting upright. Right arm extends backward behind her along the top of the couch back. Left arm hangs down loosely beside her left hip on the couch cushion. Head tilts to the left, resting against the couch back, with chin slightly up, gazing directly at the camera with a calm neutral expression. Both legs are bent sharply at the knees with knees raised high toward the camera. Left leg crosses slightly over right. The bent knees and lower legs with striped socks are prominently in the foreground, very close to the camera lens, appearing large due to wide-angle perspective distortion.

CAMERA (MATCH IMAGE 1 EXACTLY): Slightly elevated overhead angle, as if holding a phone above and in front of her face, looking down at her body reclined on the couch. Wide-angle selfie perspective that makes the legs/knees appear closer and larger.

FRAMING (MATCH IMAGE 1): Tight composition. Bottom of frame: knees and socked feet very close to lens. Middle: black leotard bodysuit and torso. Upper area: face tilted against couch back. Background: dark curtains behind couch.

OUTFIT: Black fitted leotard bodysuit with short sleeves and round neckline, form-fitting, black crew socks with three white stripes.
HAIRSTYLE: Long straight dark brown hair from Image 2 and Image 3, flowing past shoulders, NOT Image 1's black ponytail.
BACKGROUND: Dark curtains behind cream couch, moody dim lighting, natural light from right.

FACE (Image 2 and 3 ONLY): Olive-brown eyes, very pale porcelain skin, natural freckles on nose and cheeks, natural skin texture with pores, calm direct neutral gaze.

BODY (Image 4 and 5 ONLY): Very thin slender petite frame, narrow waist, slim hips, long thin legs, small A-cup, very pale porcelain ivory skin.

Photorealistic smartphone selfie, wide-angle lens, natural skin detail, 8K, moody ambient lighting.

ABSOLUTE RULES:
1. DEEP RECLINE on couch from Image 1 - NOT upright
2. OVERHEAD SELFIE camera angle from Image 1
3. KNEES DOMINATE FOREGROUND as in Image 1
4. Long dark brown hair from Image 2/3 NOT Image 1's ponytail
5. Face from Image 2/3, body from Image 4/5"""
    },
    {
        "prefix": "starbright_src2_strict_v3",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND long dark brown hairstyle.
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

POSE (IMAGE 1 IS THE ONLY POSE AUTHORITY - STRICT REPLICATION):
The subject is deeply slumped back into a cream leather couch, reclined at approximately 45 degrees. Her back presses into the couch back cushion. Right arm is thrown back lazily over the couch backrest behind her head. Left hand rests down on the couch seat beside her left hip. Her head leans to the left against the couch back, chin tilted slightly upward, looking directly into the camera. CRITICAL LEG POSITION: Both legs are bent sharply at the knees, knees pulled up high and pointing directly toward the camera. Left knee is slightly higher, crossing over right. The knees and socked feet are VERY close to the camera, creating forced perspective where legs appear large in the foreground. Black socks with white stripes visible on both feet in the bottom foreground.

CAMERA ANGLE (STRICT FROM IMAGE 1): Overhead selfie-style angle - camera is held above and slightly in front of the subject's face, pointing downward at her reclined body. Wide-angle lens creates perspective distortion making near objects (knees, feet) appear larger.

COMPOSITION (STRICT FROM IMAGE 1): Vertical portrait. Lower third: knees and socked feet dominating the foreground very close to lens. Center: black leotard bodysuit showing bare thighs. Upper third: chest, neck, face tilted against couch with head leaning left. Background: dark vertical curtain folds behind the cream couch.

OUTFIT: Black fitted leotard bodysuit with short sleeves and round neckline, form-fitting and snug, black athletic socks with three white stripes.
HAIR (IMAGE 2 AND 3 ONLY): Long straight sleek dark brown hair, past shoulders, flowing down. NOT Image 1's black ponytail.
BACKGROUND: Dark black curtains, cream/beige leather couch, dim moody lighting with window light from right.

FACE (Image 2 and 3): Olive-brown warm almond-shaped eyes, very pale porcelain ivory skin, freckles across nose and cheeks, natural lips slightly parted, calm neutral direct gaze, visible pores.

BODY (Image 4 and 5): Extremely thin slender frame, very narrow waist, slim hips, long thin legs, small A-cup, very pale porcelain skin.

Smartphone wide-angle selfie shot, 8K, photorealistic, natural skin texture, moody indoor lighting.

ABSOLUTE RULES:
1. DEEP 45-DEGREE RECLINE from Image 1 - NOT sitting up
2. OVERHEAD SELFIE camera angle looking DOWN at subject
3. KNEES and SOCKED FEET very close to camera in foreground
4. Long dark brown hair from Image 2/3 NOT black ponytail
5. Face from Image 2/3, body from Image 4/5"""
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
        "guidance_scale": 9.0,
        "enable_safety_checker": False,
        "negative_prompt": NEGATIVE_PROMPT
    }

    print(f"\n[{prefix}] Sending request (guidance_scale=9.0)...")

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
    print("SEEDream 4.5 - Source 2: STRICT POSE (guidance=9.0)")
    print("Detailed pose + forced perspective + overhead angle")
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
