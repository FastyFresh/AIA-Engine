"""
Image Quality Control Module for Starbright Monroe Pipeline
Uses Gemini Flash via OpenRouter for vision-based QC
Checks: face match, body accuracy, anatomical correctness, prompt adherence
"""
import base64, os, json, requests

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
QC_MODEL = "google/gemini-2.0-flash-001"
QC_API_URL = "https://openrouter.ai/api/v1/chat/completions"

QC_SYSTEM_PROMPT = """You are a quality control agent for AI-generated images of a specific character called "Starbright Monroe."

REFERENCE CHARACTER SPECS:
- Age appearance: 19 years old, youthful face
- Hair: Dark brown (NOT blonde, NOT red, NOT strawberry)
- Eyes: Hazel brown (NOT blue, NOT green)
- Skin: Light with visible freckles on cheeks/nose
- Build: Petite, slim, very small chest (A-B cup), slender/thin legs, narrow waist
- Overall: Natural, girl-next-door look

Your job is to analyze each generated image and return a JSON quality report. Check for:

1. FACE_MATCH: Does the face match the character specs? Check hair color, eye color, freckles, youthful appearance. Score 0-10.
2. BODY_MATCH: Is the body petite/slim with small chest and thin legs? Or is it too curvy/busty/thick? Score 0-10.
3. ANATOMY: CRITICALLY examine all body parts for correctness. This is the MOST IMPORTANT check. Be EXTREMELY strict. Look carefully for:
   - FEET: Are both feet visible and normal? Missing feet = score 0. Blurred/melted feet = score 2. Feet cut off by frame edge is OK only if intentional crop.
   - HANDS: Count fingers on each visible hand. 4 or 6+ fingers = score 0. Fused/melted fingers = score 2.
   - ARMS: Correct number (2), proper proportions, bending at natural angles.
   - LEGS: Correct number (2), natural proportions, knees bend correctly.
   - FACE: One face, two eyes, one nose, one mouth, all in correct positions.
   - TORSO: No distortion, no melting, no impossible angles.
   Score 0-10 where 10 = flawless anatomy, 0 = severe deformity.
4. PROMPT_ADHERENCE: Does the image match what was requested? (e.g., if prompt says nude but she's wearing clothes, that's a fail). Score 0-10.
5. OVERALL_QUALITY: Overall image quality, lighting, composition. Score 0-10.

Return ONLY valid JSON in this exact format:
{
  "face_match": {"score": 0, "issues": ["list of issues"]},
  "body_match": {"score": 0, "issues": ["list of issues"]},
  "anatomy": {"score": 0, "issues": ["list of issues"]},
  "prompt_adherence": {"score": 0, "issues": ["list of issues"]},
  "overall_quality": {"score": 0, "issues": ["list of issues"]},
  "total_score": 0,
  "pass": true,
  "reject_reasons": ["list of critical reasons if rejected"]
}

PASS threshold: total_score >= 35 (out of 50) AND anatomy >= 6 AND face_match >= 5
Any anatomy score below 6 is an automatic FAIL (deformities are unacceptable).
Any face_match below 5 means it doesn't look like Starbright."""


def qc_image(image_path, prompt_used="", min_score=35):
    """Run QC on a single image. Returns QC report dict."""
    if not OPENROUTER_API_KEY:
        env_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not env_key:
            return {"error": "No OpenRouter API key", "pass": False}

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    user_msg = "Analyze this AI-generated image for quality control."
    if prompt_used:
        user_msg += " The generation prompt was: \"%s\"" % prompt_used

    try:
        resp = requests.post(
            QC_API_URL,
            headers={
                "Authorization": "Bearer %s" % (OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")),
                "Content-Type": "application/json",
            },
            json={
                "model": QC_MODEL,
                "max_tokens": 1000,
                "messages": [
                    {"role": "system", "content": QC_SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_msg},
                        {"type": "image_url", "image_url": {
                            "url": "data:image/png;base64,%s" % img_b64
                        }}
                    ]}
                ]
            },
            timeout=30
        )

        if resp.status_code != 200:
            return {"error": "API error %d: %s" % (resp.status_code, resp.text[:200]), "pass": False}

        content = resp.json()["choices"][0]["message"]["content"]
        # Extract JSON from response (may be wrapped in markdown)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        report = json.loads(content.strip())

        # Enforce pass/fail logic
        total = report.get("total_score", 0)
        anatomy = report.get("anatomy", {}).get("score", 0)
        face = report.get("face_match", {}).get("score", 0)

        report["pass"] = (total >= min_score and anatomy >= 6 and face >= 5)
        if not report["pass"]:
            reasons = []
            if total < min_score:
                reasons.append("Total score %d < %d threshold" % (total, min_score))
            if anatomy < 6:
                reasons.append("Anatomy score %d < 6 (deformities)" % anatomy)
            if face < 5:
                reasons.append("Face match %d < 5 (not Starbright)" % face)
            report["reject_reasons"] = reasons

        return report

    except json.JSONDecodeError as e:
        return {"error": "Failed to parse QC response: %s" % str(e), "pass": False, "raw": content[:500]}
    except Exception as e:
        return {"error": str(e), "pass": False}


def qc_batch(image_paths, prompts=None, min_score=35):
    """Run QC on a batch of images. Returns list of (path, report) tuples."""
    results = []
    for i, path in enumerate(image_paths):
        prompt = prompts[i] if prompts and i < len(prompts) else ""
        print("  QC [%d/%d] %s" % (i+1, len(image_paths), os.path.basename(path)))
        report = qc_image(path, prompt, min_score)
        passed = report.get("pass", False)
        total = report.get("total_score", "?")
        print("    %s (score: %s)" % ("PASS" if passed else "REJECT", total))
        if not passed and report.get("reject_reasons"):
            for r in report["reject_reasons"]:
                print("    - %s" % r)
        results.append((path, report))
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 qc_module.py <image_path> [prompt]")
        sys.exit(1)
    path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else ""
    report = qc_image(path, prompt)
    print(json.dumps(report, indent=2))
