"""
SEEDream 4.5 Enhanced 5-Reference Transformation (Feb 6, 2026 workflow)

Reference order:
- Image 1: Pose/outfit/hairstyle reference (source image)
- Image 2: Face reference #1 (starbright_face_reference_v3.webp)
- Image 3: Face reference #2 (starbright_face_canonical.png)
- Image 4: Body reference #1 (body_reference_goal.webp)
- Image 5: Body reference #2 (body_reference_ivory.webp)
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

PROMPT = """CRITICAL INSTRUCTION: You MUST replicate the EXACT pose, body position, limb placement, camera angle, and framing from Image 1 with pixel-level precision.

Using Image 1 as the STRICT pose, outfit, hairstyle, camera angle, and composition reference.
Using Image 2 for facial identity ONLY (NOT hairstyle, NOT pose).
Using Image 3 as second facial identity reference ONLY (NOT hairstyle, NOT pose).
Using Image 4 for body proportions and skin tone ONLY (NOT pose).
Using Image 5 as second body reference for body shape and skin tone ONLY (NOT pose).

POSE (COPY EXACTLY FROM IMAGE 1):
Standing upright with body slightly angled to the left, right arm extended up and to the right gripping onto white sheer curtain fabric at head height, left hand resting near left hip with fingers slightly extended and curled, head tilted slightly to the right with a warm smile, shoulders relaxed and slightly back, weight distributed on both legs with subtle hip shift to the left, camera angle straight on at chest level, full body visible from head to upper thighs.

OUTFIT (FROM IMAGE 1): Red floral lace crop top with thin spaghetti straps and matching red floral lace tie-side bottoms with red ribbon ties on both hips.
HAIRSTYLE (FROM IMAGE 1 ONLY): Shoulder-length dark brown wavy hair, soft loose waves framing the face, volume at the sides. IGNORE hairstyle in Image 2 and Image 3.
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
3. Hair from Image 1 ONLY
4. Face identity from Image 2 and Image 3 ONLY
5. Body proportions from Image 4 and Image 5 ONLY"""

NEGATIVE_PROMPT = "cartoon, anime, illustration, painting, blue eyes, grey eyes, green eyes, wavy hair, curly hair, short hair, bob haircut, pixie cut, extra limbs, extra fingers, deformed, blurry skin, plastic skin, airbrushed, overly smooth skin, mannequin, tan skin, dark skin, different face, wrong face, different person, muscular, thick thighs, wide hips, large breasts, extra arms, extra legs, mutated hands, fused fingers, too many fingers, missing fingers, bad anatomy, different pose, wrong pose, different angle, wrong camera angle, multiple people, two people"


def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/png")
    return f"data:{mime};base64,{data}"


async def transform():
    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not configured")
        return None

    for p in [POSE_SOURCE, FACE_REF_1, FACE_REF_2, BODY_REF_1, BODY_REF_2]:
        if not Path(p).exists():
            print(f"ERROR: Missing file: {p}")
            return None

    print("Encoding 5 reference images...")
    pose_b64 = encode_image(POSE_SOURCE)
    face1_b64 = encode_image(FACE_REF_1)
    face2_b64 = encode_image(FACE_REF_2)
    body1_b64 = encode_image(BODY_REF_1)
    body2_b64 = encode_image(BODY_REF_2)

    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": PROMPT,
        "image_urls": [
            pose_b64,
            face1_b64,
            face2_b64,
            body1_b64,
            body2_b64,
        ],
        "image_size": {"width": 1080, "height": 1350},
        "num_images": 1,
        "max_images": 1,
        "guidance_scale": 7.0,
        "enable_safety_checker": False,
        "negative_prompt": NEGATIVE_PROMPT
    }

    print("=" * 60)
    print("SEEDream 4.5 Enhanced 5-Reference Transformation")
    print("=" * 60)
    print(f"Image 1 (Pose):   {POSE_SOURCE}")
    print(f"Image 2 (Face 1): {FACE_REF_1}")
    print(f"Image 3 (Face 2): {FACE_REF_2}")
    print(f"Image 4 (Body 1): {BODY_REF_1}")
    print(f"Image 5 (Body 2): {BODY_REF_2}")
    print(f"Guidance Scale:   7.0")
    print(f"Output Size:      1080x1350 (4:5 portrait)")
    print("=" * 60)
    print("Sending request to fal.ai...")

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                FAL_SEEDREAM_URL,
                headers=headers,
                json=payload
            )

            print(f"Response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                images = result.get("images", [])

                if images:
                    img_url = images[0].get("url", "")
                    if img_url:
                        print("Downloading generated image...")
                        img_resp = await client.get(img_url)
                        if img_resp.status_code == 200:
                            Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"starbright_5ref_{timestamp}.png"
                            filepath = Path(OUTPUT_DIR) / filename
                            filepath.write_bytes(img_resp.content)

                            print(f"\nSUCCESS! Image saved: {filepath}")
                            print(f"Seed: {result.get('seed', 'N/A')}")
                            return str(filepath)

                print("ERROR: No images in response")
                print(result)
                return None

            else:
                print(f"API error {response.status_code}: {response.text[:1000]}")
                return None

    except httpx.TimeoutException:
        print("ERROR: Request timed out (>300s)")
        return None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None


if __name__ == "__main__":
    result = asyncio.run(transform())
    if result:
        print(f"\n5-reference transformation complete! Output: {result}")
    else:
        print("\nTransformation failed.")
