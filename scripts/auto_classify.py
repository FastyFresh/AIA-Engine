#!/usr/bin/env python3
"""
Auto-classify Starbright Monroe images into tiers and ratings using GPT-4o vision.
Reads all images from content folders, classifies each, and saves to content_classification.json.
"""

import os
import sys
import json
import base64
import time
import argparse
from pathlib import Path
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    print("Installing openai...")
    os.system(f"{sys.executable} -m pip install openai -q")
    from openai import OpenAI

try:
    import anthropic
except ImportError:
    print("Installing anthropic...")
    os.system(f"{sys.executable} -m pip install anthropic -q")
    import anthropic

# --- Config ---
CLASSIFICATION_FILE = Path("/root/aia-engine/data/content_classification.json")
APPROVAL_FILE = Path("/root/aia-engine/data/starbright_approval_tracking.json")

IMAGE_DIRS = [
    "/root/starbright-studio/content/google_photos_album1",
    "/root/starbright-studio/content/google_photos_album2",
    "/root/aia-engine/content/generated",
    "/root/aia-engine/content/transform_v3",
    "/root/aia-engine/content/transform_input",
    "/root/aia-engine/content/seedream4_output",
    "/root/starbright-studio/output/images",
]

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

CLASSIFICATION_PROMPT = """You are classifying images of an AI-generated virtual influencer named Starbright Monroe for a content tier system.

Classify this image into BOTH a tier and a rating:

TIERS (content access level):
- "free" — Safe for public posting. Casual, lifestyle, fashion, selfies. Fully clothed.
- "companion" — Flirty, suggestive. Lingerie, swimwear, revealing outfits, seductive poses. Nothing explicit.
- "vip" — Explicit or near-explicit. Nudity, very revealing, intimate/sexual content.

RATINGS (content rating):
- "sfw" — Completely safe for work. No suggestive elements.
- "suggestive" — Flirty or mildly provocative but no nudity.
- "nsfw" — Partial nudity, very revealing, or sexually suggestive.
- "explicit" — Full nudity or overtly sexual content.

Respond with ONLY valid JSON, no markdown formatting:
{"tier": "free|companion|vip", "rating": "sfw|suggestive|nsfw|explicit"}
"""


def load_classification() -> dict:
    if CLASSIFICATION_FILE.exists():
        with open(CLASSIFICATION_FILE) as f:
            return json.load(f)
    return {}


def save_classification(data: dict):
    CLASSIFICATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CLASSIFICATION_FILE, "w") as f:
        json.dump(data, f, indent=2)


def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_mime_type(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "image/png")


def classify_image_anthropic(client, image_path: str, model: str = "claude-sonnet-4-20250514") -> dict:
    """Classify a single image using Anthropic Claude vision."""
    b64 = encode_image(image_path)
    mime = get_mime_type(image_path)

    response = client.messages.create(
        model=model,
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": CLASSIFICATION_PROMPT},
                ],
            }
        ],
    )

    text = response.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(text)
        if result.get("tier") not in ("free", "companion", "vip"):
            result["tier"] = "free"
        if result.get("rating") not in ("sfw", "suggestive", "nsfw", "explicit"):
            result["rating"] = "unknown"
        return result
    except json.JSONDecodeError:
        print(f"  ⚠️  Bad response: {text}")
        return {"tier": "free", "rating": "unknown"}


def classify_image_openrouter(client: OpenAI, image_path: str, model: str = "anthropic/claude-sonnet-4") -> dict:
    """Classify a single image using OpenRouter (Claude or other vision models)."""
    b64 = encode_image(image_path)
    mime = get_mime_type(image_path)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": CLASSIFICATION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64}",
                            "detail": "low",
                        },
                    },
                ],
            }
        ],
        max_tokens=100,
        temperature=0,
    )

    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(text)
        if result.get("tier") not in ("free", "companion", "vip"):
            result["tier"] = "free"
        if result.get("rating") not in ("sfw", "suggestive", "nsfw", "explicit"):
            result["rating"] = "unknown"
        return result
    except json.JSONDecodeError:
        print(f"  ⚠️  Bad response: {text}")
        return {"tier": "free", "rating": "unknown"}


def classify_image(client, image_path: str, model: str = "gpt-4o", provider: str = "openai") -> dict:
    """Route to the appropriate classifier."""
    if provider == "anthropic":
        return classify_image_anthropic(client, image_path, model)
    elif provider == "openrouter":
        return classify_image_openrouter(client, image_path, model)
    else:
        # Original OpenAI path
        b64 = encode_image(image_path)
        mime = get_mime_type(image_path)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": CLASSIFICATION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64}",
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            max_tokens=100,
            temperature=0,
        )
        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            result = json.loads(text)
            if result.get("tier") not in ("free", "companion", "vip"):
                result["tier"] = "free"
            if result.get("rating") not in ("sfw", "suggestive", "nsfw", "explicit"):
                result["rating"] = "unknown"
            return result
        except json.JSONDecodeError:
            print(f"  ⚠️  Bad response: {text}")
            return {"tier": "free", "rating": "unknown"}


def collect_images() -> list:
    """Collect all images from content directories."""
    images = []
    for dir_path in IMAGE_DIRS:
        if not os.path.isdir(dir_path):
            continue
        for fname in sorted(os.listdir(dir_path)):
            if Path(fname).suffix.lower() in IMAGE_EXTS:
                images.append({
                    "filename": fname,
                    "path": os.path.join(dir_path, fname),
                    "dir": dir_path,
                })
    return images


def main():
    parser = argparse.ArgumentParser(description="Auto-classify Starbright images")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be classified without calling API")
    parser.add_argument("--limit", type=int, default=0, help="Max images to classify (0=all)")
    parser.add_argument("--force", action="store_true", help="Re-classify already classified images")
    parser.add_argument("--model", default="gpt-4o", help="Vision model to use")
    parser.add_argument("--provider", default="anthropic", choices=["openai", "anthropic", "openrouter"],
                        help="API provider (default: anthropic)")
    args = parser.parse_args()

    # Load existing classifications
    classifications = load_classification()
    already_classified = set(classifications.keys())

    # Collect all images
    all_images = collect_images()
    print(f"📁 Found {len(all_images)} total images on disk")

    # Filter to unclassified
    if args.force:
        to_classify = all_images
    else:
        to_classify = [img for img in all_images if img["filename"] not in already_classified]

    print(f"🔍 Already classified: {len(already_classified)}")
    print(f"📋 To classify: {len(to_classify)}")

    if args.limit > 0:
        to_classify = to_classify[:args.limit]
        print(f"⚡ Limited to: {len(to_classify)}")

    if args.dry_run:
        print("\n🏃 DRY RUN — would classify:")
        for img in to_classify[:20]:
            print(f"  {img['filename']}")
        if len(to_classify) > 20:
            print(f"  ... and {len(to_classify) - 20} more")
        return

    # Load API keys from .env
    env_vars = {}
    env_file = Path("/root/aia-engine/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip()

    # Initialize client based on provider
    provider = args.provider
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY") or env_vars.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("❌ No ANTHROPIC_API_KEY found")
            sys.exit(1)
        client = anthropic.Anthropic(api_key=api_key)
        if args.model == "gpt-4o":
            args.model = "claude-sonnet-4-20250514"  # default to Sonnet for Anthropic
        print(f"🔑 Using Anthropic ({args.model})")

    elif provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY") or env_vars.get("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ No OPENROUTER_API_KEY found")
            sys.exit(1)
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        if args.model == "gpt-4o":
            args.model = "anthropic/claude-sonnet-4"
        print(f"🔑 Using OpenRouter ({args.model})")

    else:
        api_key = os.environ.get("OPENAI_API_KEY") or env_vars.get("OPENAI_API_KEY")
        if not api_key:
            print("❌ No OPENAI_API_KEY found")
            sys.exit(1)
        client = OpenAI(api_key=api_key)
        print(f"🔑 Using OpenAI ({args.model})")

    # Classify
    stats = {"free": 0, "companion": 0, "vip": 0}
    rating_stats = {"sfw": 0, "suggestive": 0, "nsfw": 0, "explicit": 0, "unknown": 0}
    errors = 0
    
    print(f"\n🚀 Starting classification with {args.model}...\n")

    for i, img in enumerate(to_classify):
        fname = img["filename"]
        fpath = img["path"]
        
        try:
            result = classify_image(client, fpath, model=args.model, provider=provider)
            tier = result["tier"]
            rating = result["rating"]

            classifications[fname] = {
                "tier": tier,
                "rating": rating,
                "updated": datetime.now().isoformat(),
                "source_dir": img["dir"],
                "model": args.model,
            }

            stats[tier] = stats.get(tier, 0) + 1
            rating_stats[rating] = rating_stats.get(rating, 0) + 1

            emoji = {"free": "🟢", "companion": "🟡", "vip": "🔴"}.get(tier, "⚪")
            print(f"  [{i+1}/{len(to_classify)}] {emoji} {fname} → {tier} / {rating}")

            # Save every 10 images (checkpoint)
            if (i + 1) % 10 == 0:
                save_classification(classifications)
                print(f"  💾 Checkpoint saved ({i+1} done)")

            # Rate limit: ~20 requests/min to be safe
            time.sleep(0.5)

        except Exception as e:
            print(f"  [{i+1}/{len(to_classify)}] ❌ {fname}: {e}")
            errors += 1
            time.sleep(2)  # Back off on errors

    # Final save
    save_classification(classifications)

    # Summary
    print(f"\n{'='*50}")
    print(f"✅ Classification complete!")
    print(f"{'='*50}")
    print(f"  Processed: {len(to_classify)}")
    print(f"  Errors: {errors}")
    print(f"\n  📊 Tier breakdown:")
    for tier, count in sorted(stats.items()):
        emoji = {"free": "🟢", "companion": "🟡", "vip": "🔴"}.get(tier, "⚪")
        print(f"    {emoji} {tier}: {count}")
    print(f"\n  📊 Rating breakdown:")
    for rating, count in sorted(rating_stats.items()):
        print(f"    {rating}: {count}")
    print(f"\n  💾 Saved to: {CLASSIFICATION_FILE}")


if __name__ == "__main__":
    main()
