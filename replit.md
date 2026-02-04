# AIA Engine - Replit Hub Edition

*Last Updated: February 4, 2026*

## Overview
The Autonomous AI Influencer Agent Engine is a multi-agent system designed to generate hyper-realistic, photorealistic AI influencer content for multiple personas (Starbright Monroe, Luna Vale) under Firepie LLC. It automates content creation, optimization, and multi-platform distribution using a "micro-loop workflow" which combines curated hero images with micro-movement video generation.

**Primary Monetization:** DFans (dfans.co/starbrightnight)
**Content Distribution Funnel:** Instagram/TikTok (teasers) → Bio Link → Linktree → starbrightnights.com → DFans (premium)
**Status:** Telegram monetization deprecated (0% conversion from 18 users)

### Micro-Loop Workflow (Complete)
Hero image → Kling v2.1 micro-movement video → Grok captions → Grok hashtags (no AI tags) → DFans CTA → Twitter/X posting

---

## Replicate SEEDream 4.5 Reference Image Workflow

### Core Technology
The system uses **ByteDance SEEDream 4.5** via Replicate API for hyper-realistic image generation with multi-reference image conditioning. This enables consistent face, body, and background preservation across all generated images.

### API Endpoint
```
POST /api/seedream4/generate
```

### Replicate Model
```
bytedance/seedream-4.5
```

### Reference Image System

SEEDream 4.5 supports up to **10 reference images** for identity consistency. The system uses a multi-reference approach:

| Reference Type | Purpose | Location |
|----------------|---------|----------|
| **Face Reference** | Locks facial features, expressions, freckles | `content/references/{influencer}/` |
| **Body Reference** | Maintains body proportions, skin tone, figure | `content/references/{influencer}/` |
| **Background Reference** | (Optional) Scene consistency | `content/references/backgrounds/` |

### Current Reference Images

**Starbright Monroe:**
```
Face:  content/references/starbright_monroe/starbright_face_reference_v3.png
Body:  content/references/starbright_monroe/body_reference.png
Back:  content/references/starbright_monroe/body_reference_back_1.png
```

**Luna Vale:**
```
Face:  content/references/luna_vale/luna_face_canonical.png
Body:  content/references/luna_vale/luna_body_reference.png
```

### Key API Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `image_input` | Array of base64 images | Face + body (+ optional background) references |
| `aspect_ratio` | `3:4` (portrait), `9:16` (full-body) | Image dimensions |
| `size` | `4K` | Resolution for maximum skin detail |
| `max_images` | `1` | Images per generation |
| `guidance_scale` | `2.5` - `6.0` | Prompt adherence (lower = more creative) |
| `seed` | Integer | Lock for reproducibility across session |
| `negative_prompt` | String | Anatomical/quality exclusions |

### Default Negative Prompt (Anatomical Safety)
```
extra limbs, extra legs, extra arms, extra fingers, missing limbs, 
deformed body, disproportionate body, unnatural anatomy, distorted proportions, 
elongated limbs, stretched arms, stretched legs, unrealistic limb length, 
mutated hands, fused fingers, too many fingers, missing fingers, 
bad anatomy, wrong anatomy, unrealistic body, mannequin, plastic skin
```

### Prompt Structure (Proven Format)
```
[POSE + SETTING], [OUTFIT], [IDENTITY DESCRIPTORS], [CAMERA ANGLE], [LIGHTING], [EXPRESSION]
```

### Identity Descriptors (Critical for Quality)

**Starbright Monroe (HIGH DETAIL - Best Results):**
```
very pale porcelain ivory white skin, straight sleek dark brown hair (not wavy, not curly), 
warm olive-brown eyes, natural freckles across nose and cheeks, 
extremely thin slender petite body with very narrow tiny waist, 
slim narrow hips, long thin slender legs, delicate small frame, size 0 figure,
small natural A-cup breasts, proportionate feminine figure
```

**Luna Vale:**
```
fair pale skin with subtle freckles across nose and cheeks, 
long straight cotton candy pink hair parted in middle, 
striking grey-blue eyes with long dark lashes, thick natural eyebrows, 
soft rounded face with defined cheekbones, full pouty natural lips, 
slim petite body with feminine curves, small waist, 
youthful delicate features, natural beauty with minimal makeup look
```

### Camera & Quality Settings
```
Shot on Canon EOS R5, 85mm f/1.4 lens
natural skin texture with visible pores
8K ultra detailed, cinematic lighting
```

### Hyper-Realism Settings
```
natural skin texture with visible pores, fine skin detail, 
slight natural skin imperfections, photorealistic skin tones, 
no plastic skin, no airbrushed, no over-smoothed, no beauty filter
```

### Python Example (Using System Service)
```python
from app.services.seedream4_service import Seedream4Service

service = Seedream4Service(influencer_id="starbright_monroe")

result = await service.generate_with_background(
    prompt="Full body portrait, standing confidently in luxury apartment, wearing white silk dress, soft natural lighting",
    face_ref=None,  # Uses default from config
    body_ref=None,  # Uses default from config
    background_ref="content/references/backgrounds/luxury_apartment.png",  # Optional
    aspect_ratio="3:4",
    size="4K",
    filename_prefix="starbright_apartment"
)
```

### Direct Replicate API Example
```python
import replicate

output = replicate.run(
    "bytedance/seedream-4.5",
    input={
        "prompt": "Professional headshot, studio lighting, soft expression",
        "image_input": [
            face_base64_url,
            body_base64_url
        ],
        "aspect_ratio": "3:4",
        "size": "4K",
        "guidance_scale": 2.5,
        "seed": 12345,
        "negative_prompt": "extra limbs, deformed body, plastic skin..."
    }
)
```

### Best Practices

1. **Face Consistency:** Use 2-3 clear face references (front + 3/4 angle)
2. **Lock Seed:** Keep same seed across a session for identity stability
3. **Guidance Scale:** 2.5-3.0 for natural results, 4.5-6.0 for strict prompt adherence
4. **Match Camera Angles:** Reference image angle should match desired output angle
5. **Detailed Identity:** More specific descriptors = better quality (skin tone + hair texture + eye color + body details + distinguishing features)

### Service Hierarchy
- **PRIMARY:** `app/services/fal_seedream_service.py` (fal.ai) - faster, cheaper
- **FALLBACK:** `app/services/seedream4_service.py` (Replicate) - multi-reference support

### Prompt Builder Service
Location: `app/services/prompt_builder.py`

Centralizes:
- Identity descriptions per influencer
- Camera settings (Canon EOS R5, 85mm f/1.4)
- Hyper-realism settings (visible pores, natural texture)
- Quality settings (8K ultra detailed)

### Content Output Directories
```
content/seedream4_output/     # Raw generated images
content/final/{influencer}/   # Approved/curated images
content/generated/{influencer}/ # Legacy output directory
```

---

## SEEDream 4.5 Multi-Reference Transformation Workflow (Feb 4, 2026 - PRODUCTION READY)

### Overview
This workflow transforms a reference pose image into Starbright Monroe using 4 reference images for optimal control over pose, identity, and environment. SEEDream 4.5 supports up to 10 reference images.

### Reference Image Order (Critical)
The order of images in `image_urls` determines how SEEDream interprets each reference:

| Position | Purpose | Example |
|----------|---------|---------|
| Image 1 | Pose/outfit reference | Source image with desired pose and clothing |
| Image 2 | Face reference | Starbright's hyper-realistic face with skin texture |
| Image 3 | Body reference | Starbright's body proportions and physique |
| Image 4 | Background reference | Target environment/setting |

### Optimal Prompt Structure
Use explicit reference assignment pattern - tell the model exactly what to take from each image:

```
Using Image 1 for pose, outfit and camera angle.
Using Image 2 for facial features, skin texture, and facial structure.
Using Image 3 for body proportions, body type, and physique.
Using Image 4 for background environment and lighting.

Generate a hyper-realistic photograph of a young woman:
- Face: Take exact facial features from Image 2 - the olive-brown eyes, natural skin texture with visible pores, subtle freckles, dark brown hair color, and facial bone structure. Preserve all minor skin imperfections and realistic skin details.
- Body: Apply the slim petite body type from Image 3 - extremely thin slender frame, very narrow tiny waist, slim hips, long thin legs.
- Pose: Replicate the exact pose, body position, and camera angle from Image 1. Keep the clothing style from Image 1.
- Background: Place the subject in the environment from Image 4.

Style: Shot on Canon EOS R5, 85mm f/1.4 lens, shallow depth of field, professional fashion photography.
Skin: Hyper-realistic with natural texture, visible pores, subtle imperfections, minor skin flaws for authenticity.
Lighting: Match lighting from Image 4 environment.

Preserve facial identity from Image 2 unchanged.
Preserve body proportions from Image 3 unchanged.
Keep pose and outfit from Image 1.
Match background and lighting from Image 4.
```

### API Endpoint (fal.ai)
```
POST https://fal.run/fal-ai/bytedance/seedream/v4.5/edit
```

### Python Implementation
```python
import httpx
import base64
from pathlib import Path

FAL_URL = "https://fal.run/fal-ai/bytedance/seedream/v4.5/edit"

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", 
            ".png": "image/png", ".webp": "image/webp"}.get(ext, "image/png")
    return f"data:{mime};base64,{data}"

# Encode all 4 references
pose_b64 = encode_image("path/to/pose_reference.jpg")
face_b64 = encode_image("path/to/starbright_face.webp")
body_b64 = encode_image("path/to/starbright_body.webp")
bg_b64 = encode_image("path/to/background.png")

payload = {
    "prompt": MULTI_REF_PROMPT,  # See prompt structure above
    "image_urls": [pose_b64, face_b64, body_b64, bg_b64],  # Order matters!
    "image_size": "auto_4K",
    "num_images": 1,
    "max_images": 1,
    "enable_safety_checker": False,
    "negative_prompt": "cartoon, anime, illustration, blue eyes, grey eyes, black hair, wavy hair, curly hair, extra limbs, deformed, blurry skin, plastic skin, airbrushed, overly smooth skin"
}

headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
response = await httpx.AsyncClient().post(FAL_URL, headers=headers, json=payload)
```

### Script Location
```
scripts/transform_seedream_multi_ref.py
```

### Key Best Practices

1. **Explicit Reference Assignment**: Always specify "Using Image X for Y" at the start of the prompt
2. **Preservation Rules**: End the prompt with explicit preservation commands for each element
3. **Hyper-Realism**: Include "visible pores, subtle imperfections, minor skin flaws" for authentic skin
4. **Negative Prompt**: Block smooth/plastic skin and wrong identity features (wrong eye color, hair type)
5. **Image Size**: Use `auto_4K` for maximum quality and detail retention

### Comparison with Other Methods

| Method | Pose Control | Identity Control | Best For |
|--------|--------------|------------------|----------|
| SEEDream Multi-Ref (4 images) | Good | Excellent | Full character transformation |
| ControlNet + Face Swap | Excellent | Good | Exact pose matching |
| SEEDream (2 refs: face+body) | Loose | Good | Quick generations |

### Output
Results saved to: `content/seedream4_output/starbright_multiref_*.png`

---

## Pose Transfer Workflow (Jan 24, 2026 - PRODUCTION READY)

**Endpoint:** `POST /api/seedream4/generate`
**Documentation:** `docs/SEEDREAM4_POSE_TRANSFER_WORKFLOW.md`

**Settings:**
- Aspect ratio: `3:4` (portrait)
- Provider: Replicate Seedream 4.5

**Success Rate:** 75% (9/12 images) - Some lingerie prompts flagged
**Key Insight:** Match camera angle from reference image exactly

**References:**
- Face reference: `content/references/starbright_monroe/starbright_face_reference_v3.png`
- Alluring pose library: `content/prompt_templates/alluring_pose_library.json`

---

## User Preferences
- Prefers proper training convergence over fast incomplete training
- Values clean, organized architecture without disabled code stubs
- Needs reliable Replicate API integration for production-quality results
- Wants future agent interfaces documented for roadmap clarity
- Prefers unified interface over multiple separate tools
- Prioritizes face shape and body consistency across all images
- Use 9:16 aspect ratio for full-body images
- Both personas use micro-loop workflow with curated hero images from KreatorFlow
- No AI-related hashtags - All hashtags must avoid #aimodel, #aigirl, #aibeauty, etc.
- Dynamic hashtags optimized for maximum reach via Grok AI
- DFans is primary monetization channel (NSFW content required)

## System Architecture

### UI/UX Decisions
The system features a unified React/TypeScript dashboard providing system monitoring, content galleries with approval workflows, tools for managing hero images and captions, an enhanced Twitter share dialog, analytics, posting queue management, and a "Research" tab for competitor analysis and prompt library management.

### Technical Implementations & Feature Specifications
- **Micro-Loop Workflow**: Core content generation combining curated hero images, micro-movement video generation (Kling v2.1), persona-specific captions, dynamic AI-optimized hashtags, and automated Twitter/X posting.
- **Content Optimization**: Dynamic hashtag optimization (Grok AI), AI-powered background music selection (FFmpeg integration), CTA optimization (Grok AI), and AI-powered content calendar scheduling.
- **Image Generation**: Primary use of Fal.ai Seedream 4.5 Edit Service with reference image conditioning for character consistency and hyper-realism (e.g., specific camera specs, natural skin texture, 8K detail). Includes prompt variation service to prevent repetition and multi-influencer support.
- **Multi-Agent System**: An orchestrator manages specialized agents for persona identity, video generation, content generation, captioning, optimization, scheduling, posting, and research.
- **Instagram Research Agent**: Utilizes Apify for scraping Instagram profiles and Grok Vision for visual analysis to generate research-driven prompts.
- **Prompt Safety Filter**: Word-boundary-aware vocabulary transformation to prevent content policy violations.
- **Video/Reel Generation**: Fal.ai Kling v2.1 for image-to-video generation.
- **Video Character Replacement**: Wan-2.2 Animate Replace service for character replacement in videos while preserving scene dynamics.
- **Content Storage**: Local filesystem (`content/`) + Replit Object Storage for persistent cloud assets.
- **Telegram Monetization System (DEPRECATED)**: Code preserved in `app/telegram/` but workflow stopped. 0% conversion from 18 users. DFans is now primary monetization target.

### System Design Choices
- **Multi-Influencer Architecture**: Supports multiple AI influencers with isolated configurations and independent workflows.
- **Custom LoRA Support**: Fal.ai LoRA service for custom safetensor LoRA model uploads and generation (e.g., "Starbright18" trigger word).
- **Reference Image Alternative**: Seedream4 dual-reference images for identity consistency without LoRA training.
- **Service Consolidation**: PromptSafetyFilter and PromptBuilder extracted into standalone services.
- **API Route Modularization**: Main FastAPI app split into focused routers in `app/api/`:
  - `admin_routes.py`: Admin dashboard and authentication
  - `payment_routes.py`: Stripe webhooks and payment pages
  - `micro_loop_routes.py`: Micro-loop video generation and caption endpoints
  - `telegram_api_routes.py`: (DEPRECATED) Telegram bot management endpoints
- **Python Backend**: FastAPI, Uvicorn, Pydantic.
- **React Frontend**: Vite, React, TypeScript, Tailwind CSS, shadcn/ui.
- **Modular Telegram Bot Architecture (DEPRECATED)**: Logic in `app/telegram/` - preserved but inactive.
- **Object Storage**: Replit Object Storage (S3-compatible) for persistent content assets. Service at `app/services/object_storage/`.
- **Database Migrations**: Version-tracked migrations for schema management.
- **Centralized Settings**: Pydantic for configuration management.
- **Image Generation Interface**: Abstract base class with a factory pattern to switch between SFW (Fal.ai Seedream 4.5) and potential NSFW providers.
- **Luna Modular Prompt System (V1)**: Tiered outfit system (Tier 1 weeks 1-3, Tier 2 weeks 4-6, Tier 3 after traction), modular background/vibe categories, safety guardrails (19+ only, no teen framing), and batch generation with outfit consistency. Config stored in `content/luna_prompt_config.json`.

### Critical Discovery: Detailed Identity Prompts (Dec 30, 2024)
The quality of generated images is directly correlated to the level of detail in the identity prompt. **Starbright's detailed identity produces significantly better results.**

**Key Insight:** The `/api/seedream4/generate-quick` endpoint always uses Starbright's detailed prompt (ignores `influencer` parameter). This is why "Luna" generations look like high-quality Starbright images.

**Action Items:**
- Keep using Starbright's detailed prompt structure for best results
- To improve Luna quality, update her identity with equally detailed descriptors
- The magic formula: specific skin tone + specific hair texture + specific eye color + detailed body descriptors + specific freckles/features

## External Dependencies

### APIs
- **Replicate API**: For Kling v2.1 (micro-movement videos) and Seedream 4.5 (image generation).
- **XAI/Grok API**: For caption generation, hashtag optimization, and Grok Vision (image analysis).
- **Twitter API**: OAuth 1.0a (media uploads) and OAuth 2.0 (text posts).
- **Apify API**: Instagram profile/post scraping.
- **Fal.ai API**: For Seedream 4.5 hyper-realistic image generation.
- **Stripe API**: For payment processing and subscription management.

### Core Technologies
- **Backend**: Python (FastAPI, Uvicorn, Pydantic, httpx, python-dotenv, Tweepy).
- **Frontend**: Node.js ecosystem (Vite, React, TypeScript, Tailwind CSS, shadcn/ui).

### Environment Variables
- `FAL_KEY`
- `REPLICATE_API_TOKEN`
- `XAI_API_KEY`
- `TWITTER_CLIENT_ID`
- `TWITTER_CLIENT_SECRET`
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`
- `SESSION_SECRET`
- `APIFY_API_TOKEN`

## Prompt Templates (Jan 22, 2026)

### Starbright Kneeling Poses
Location: `content/prompt_templates/starbright_kneeling_poses.json`

Successfully developed kneeling pose series with male figure. Key learnings:

**Restraint Terminology:**
- Use "chrome wristlocks" instead of "handcuffs" to avoid loose cuff rendering issues
- "Chrome cylinder wrist locks" also works well

**Accessories:**
- Collar: "black leather dog collar with a metal O-ring around her neck"
- Wristlocks: "Both of her wrists are locked behind her back with chrome wristlocks, shiny metal restraints locked around each wrist"

**Successful Outfit Variations:**
- White ribbed dress
- Pink cotton bralette and panties
- Black mini dress with stilettos
- Red plaid skirt + white crop top (with white tights, black thigh-highs, or bare legs)
- Black two-piece bikini

**Technical Notes:**
- Use portrait_4_3 aspect ratio for this pose
- Male figure: "navy pants and white t-shirt"
- For bare feet: add shoes/stockings/tights to negative prompt
- Always include detailed identity descriptors for best results

---

## Project File Structure

```
app/
├── agents/                    # Multi-agent system
│   ├── identity_agent.py      # Persona identity management
│   ├── reference_agent.py     # Image generation with references
│   ├── quality_agent.py       # Quality assessment and tuning
│   ├── caption_agent.py       # Caption generation (Grok)
│   ├── planner_agent.py       # Content scheduling
│   ├── twitter_poster_agent.py # Twitter/X posting
│   └── ...
├── services/
│   ├── seedream4_service.py   # Replicate SEEDream 4.5 (FALLBACK)
│   ├── fal_seedream_service.py # Fal.ai SEEDream 4.5 (PRIMARY)
│   ├── prompt_builder.py      # Centralized prompt construction
│   ├── prompt_safety_filter.py # Content policy compliance
│   ├── storage_manager.py     # Disk space management
│   └── object_storage/        # Replit Object Storage integration
├── api/                       # FastAPI route modules
│   ├── seedream_routes.py     # Image generation endpoints
│   ├── workflow_routes.py     # Approval/rejection workflows
│   └── ...
├── tools/
│   ├── replicate_client.py    # Replicate API wrapper
│   ├── grok_client.py         # XAI/Grok API wrapper
│   └── ...
└── main.py                    # FastAPI app entry point

content/
├── references/
│   ├── starbright_monroe/     # Starbright reference images
│   ├── luna_vale/             # Luna reference images
│   └── backgrounds/           # Background references
├── seedream4_output/          # Raw generated images
├── final/                     # Approved curated images
├── prompt_templates/          # Pose and prompt libraries
└── luna_prompt_config.json    # Luna modular prompt config

client/                        # React/TypeScript dashboard
```

---

## Quick Reference: Image Generation

**To generate a Starbright image:**
```python
from app.services.seedream4_service import Seedream4Service

service = Seedream4Service("starbright_monroe")
result = await service.generate(
    prompt=service.build_prompt(
        scene="luxury bedroom with soft morning light",
        outfit="white silk slip dress",
        pose="sitting on edge of bed",
        lighting="soft diffused natural lighting"
    ),
    aspect_ratio="3:4",
    filename_prefix="starbright_bedroom"
)
```

**To transform an image into Starbright style:**
Use the SEEDream 4.5 reference system - provide the source image context in your prompt while using Starbright's face and body references to maintain identity consistency.

---

## Workflow Command
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000
```
