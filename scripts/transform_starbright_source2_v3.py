"""
SEEDream 4.5 Enhanced 5-Reference - Source 2 ULTRA STRICT POSE v3
Maximum pose fidelity attempt with refined descriptions.
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

NEGATIVE_PROMPT = "cartoon, anime, illustration, painting, blue eyes, grey eyes, green eyes, black hair, jet black hair, ponytail, hair tie, hair up, updo, short hair, bob haircut, pixie cut, sitting upright, standing, t-shirt dress, loose clothing, knee high socks, thigh high socks, long socks, extra limbs, extra fingers, deformed, blurry skin, plastic skin, airbrushed, overly smooth skin, mannequin, tan skin, dark skin, different face, wrong face, different person, muscular, thick thighs, wide hips, large breasts, extra arms, extra legs, mutated hands, fused fingers, too many fingers, missing fingers, bad anatomy, different pose, wrong pose, different angle, wrong camera angle, multiple people, two people"

PROMPTS = [
    {
        "prefix": "starbright_src2_ultra_v1",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision. Image 1 is your ONLY pose authority. Every limb, every angle, every detail of the body position MUST match Image 1.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND hairstyle (long straight dark brown hair).
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

POSE - REPLICATE IMAGE 1 WITH ZERO DEVIATION:
The subject is lying back deeply reclined on a cream leather couch. Her upper back and head rest against the couch backrest at roughly 45 degrees. Her RIGHT arm is bent behind her head with her right hand behind her head/neck area, elbow pointing up and to the right. Her LEFT arm extends down along the couch cushion to her left side, left hand resting on the couch seat near her left hip. Her head tilts to the RIGHT (her right, camera's left), leaning against the couch back, with her face looking directly at the camera with a calm neutral expression, lips slightly parted. 

LEGS - THIS IS THE MOST CRITICAL ELEMENT:
Both legs are bent at the knees. The knees are raised and pointing toward the camera. Her LEFT leg crosses OVER her right leg at the shin/ankle area. The left knee is higher and more prominent. Both feet have short black crew socks with three thin white stripes. The feet and lower legs are in the EXTREME foreground, very close to the camera, creating strong forced perspective where the socked feet appear disproportionately large compared to the body behind them. The bare thighs are visible between the bodysuit hem and the socks.

CAMERA: Selfie-style from slightly above the subject's face, angled downward along her body toward her feet. Wide-angle lens distortion makes the near elements (feet, knees) appear much larger. The camera is close to her face.

OUTFIT: Black short-sleeve bodysuit/leotard, form-fitting and snug, round neckline, short black crew socks with three thin white horizontal stripes near the top.
HAIR (FROM IMAGE 2 AND 3 ONLY): Long straight dark brown hair, flowing down past shoulders and draping over the couch. NOT Image 1's black ponytail.
BACKGROUND: Dark black vertical curtains behind the cream/beige leather couch, moody indoor lighting with natural light from a window on the right side.

FACE (from Image 2 and Image 3 ONLY):
  * Olive-brown warm eyes
  * Very pale porcelain ivory white skin tone
  * Natural freckles across nose and cheeks
  * Natural skin texture with visible pores
  * Calm neutral expression, lips slightly parted, direct gaze

BODY (from Image 4 and Image 5 ONLY):
  * Extremely thin slender petite frame
  * Very narrow tiny waist, slim narrow hips
  * Long thin slender legs
  * Small natural A-cup breasts
  * Very pale porcelain ivory white skin

Smartphone selfie, wide-angle lens, 8K, photorealistic, moody ambient lighting, natural skin texture.

ABSOLUTE RULES:
1. Body reclined at 45 degrees on couch from Image 1
2. Right arm bent behind head, left arm down at side
3. LEFT leg crosses OVER right, knees toward camera
4. FEET IN EXTREME FOREGROUND close to camera lens
5. Overhead selfie camera angle from Image 1
6. Long dark brown hair from Image 2/3, NOT ponytail
7. Black bodysuit NOT t-shirt"""
    },
    {
        "prefix": "starbright_src2_ultra_v2",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND hairstyle (long dark brown hair).
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

EXACT POSE REPLICATION FROM IMAGE 1:
Girl lying reclined on cream leather sofa, upper body propped against backrest at 45-degree angle. Right arm bent with right hand tucked behind her head/neck, right elbow up. Left arm relaxed down at her left side, hand resting on cushion near hip. Head tilts to her right resting against sofa back, eyes looking directly at camera, neutral sultry expression.

CRITICAL LEG POSITION FROM IMAGE 1:
Legs bent at knees, knees pointing at camera. Left leg crosses over right leg at the shins. Bare thighs visible. Short black ankle socks with three white stripes on both feet. Feet are extremely close to the camera - the socked feet are the closest objects to the lens and appear very large due to wide-angle perspective distortion. Socked feet fill the bottom-center and bottom-right of the frame.

CAMERA ANGLE FROM IMAGE 1:
Selfie shot from above and close to her face, camera pointing down the length of her reclined body toward her feet. Wide-angle smartphone lens creates strong foreshortening - feet appear huge, body recedes. Camera is positioned slightly above her eye level.

FRAMING FROM IMAGE 1:
Top of frame: dark curtain background, edge of couch backrest. Upper portion: her face tilted against couch back with arm behind head. Middle: black bodysuit on torso, bare thighs. Bottom/foreground: large prominent socked feet and crossed legs very close to camera.

OUTFIT: Black form-fitting short-sleeve bodysuit/leotard, round neck, short black crew socks with three thin white stripes.
HAIR: Long straight dark brown hair from Image 2 and 3, draping past shoulders. NOT Image 1's ponytail.
BACKGROUND: Dark black curtains, cream leather couch, moody dim with side window light.

FACE (Image 2/3): Olive-brown eyes, very pale porcelain skin, freckles on nose and cheeks, visible pores, neutral direct gaze.
BODY (Image 4/5): Very thin slender frame, narrow waist, slim hips, thin legs, small A-cup, very pale skin.

Smartphone selfie, wide-angle, 8K photorealistic, moody indoor lighting.

ABSOLUTE RULES:
1. 45-degree recline on cream couch
2. Right arm behind head, left arm at side
3. Left leg over right, knees at camera
4. Socked feet huge in foreground
5. Overhead selfie angle
6. Long brown hair from refs, NOT ponytail
7. Black bodysuit, NOT t-shirt"""
    },
    {
        "prefix": "starbright_src2_ultra_v3",
        "prompt": """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision.

Using Image 1 as the STRICT pose, outfit, camera angle, and composition reference.
Using Image 2 for facial identity AND long dark brown hairstyle.
Using Image 3 as second facial identity reference AND hairstyle reinforcement.
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

IMAGE 1 POSE - PIXEL-PERFECT COPY:
Subject reclined deeply on cream leather couch at approximately 45-degree angle, back and shoulders pressed against the couch backrest. Right arm: bent at elbow, hand behind head/neck with elbow pointing upward. Left arm: extended down along her left side, hand on couch cushion near left hip. Head: tilted to her right, resting against couch back, face angled toward camera with neutral calm expression, lips slightly parted. 

IMAGE 1 LEG POSITION - MOST IMPORTANT:
Both knees bent, pointing directly at the camera. Left leg crosses over right leg at shin level. Bare upper thighs visible between bodysuit and socks. Both feet wearing short black crew socks with 3 white stripes. The feet and lower shins are the NEAREST objects to the camera, appearing very large in the extreme foreground due to wide-angle lens foreshortening. Left foot is slightly higher than right. The socked feet take up significant space in the lower portion of the image.

IMAGE 1 CAMERA - EXACT MATCH:
Close-range selfie from slightly above face level, camera aimed downward along her reclined body. Wide-angle smartphone lens (roughly 24mm equivalent) creates dramatic perspective: face is sharp and detailed in the upper frame, body recedes in the middle, and feet appear oversized in the bottom foreground. Camera distance is intimate, approximately arm's length from face.

IMAGE 1 COMPOSITION:
Vertical 4:5 portrait. Top area: dark curtains and couch back. Upper center: face with tilted head, arm behind head. Center: black bodysuit torso. Lower center: bare thighs. Bottom foreground: oversized socked feet dominating the frame.

OUTFIT: Black short-sleeve bodysuit/leotard, form-fitting, round neckline. Short black crew socks with 3 thin white stripes. Bare thighs between bodysuit and socks.
HAIR (IMAGE 2 AND 3): Long straight dark brown hair flowing past shoulders, draped over couch. NOT the black ponytail from Image 1.
BACKGROUND: Dark vertical curtain folds behind couch, cream/beige leather couch, dim moody indoor light with natural window light from right.

FACE (Image 2/3): Olive-brown warm eyes, very pale porcelain ivory skin, natural freckles on nose and cheeks, natural pores, calm neutral direct gaze.
BODY (Image 4/5): Extremely thin slender petite frame, very narrow waist, slim hips, long thin legs, small A-cup, very pale porcelain skin.

Smartphone wide-angle selfie, 8K photorealistic, natural skin texture, moody indoor lighting.

ABSOLUTE RULES:
1. 45-degree deep recline on cream couch - NOT upright
2. Right hand behind head, left hand at side on cushion
3. Left leg crosses over right at shins, knees at camera
4. Socked feet DOMINATE foreground, appearing oversized
5. Close selfie overhead angle with wide-angle distortion
6. Long dark brown hair from Image 2/3 NOT ponytail
7. Black bodysuit/leotard NOT t-shirt or dress"""
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
    print("SEEDream 4.5 - Source 2: ULTRA STRICT POSE v3")
    print("Guidance=9.0 | Bodysuit | Detailed limb positions")
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
