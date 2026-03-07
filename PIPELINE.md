# Starbright Monroe — Content Pipeline Harness
> Last updated: 2026-02-23 | Pipeline: Seedream 4.5 Edit | Status: ACTIVE

## Quick Reference

| Component | Path | Purpose |
|-----------|------|---------|
| **Generation script** | `/root/aia-engine/nsfw_pipeline_seedream.py` | Batch generation with 2-ref conditioning |
| **Transform script** | `/root/aia-engine/nsfw_transform.py` | 5-ref identity swap on existing images |
| **Reference images** | `/root/aia-engine/content/references/starbright_monroe/advanced/` | Character reference photos |
| **Output directory** | `/root/aia-engine/content/generated/starbright_monroe/` | Generated images land here |
| **Transforms dir** | `/root/aia-engine/content/generated/starbright_monroe/transforms/` | Transform outputs |
| **Gallery server** | `http://localhost:8888` | Image review & approval (port 8888) |
| **Hub API** | OpenClaw Hub (Replit) | Web UI for pipeline control |
| **Fal.ai endpoint** | `https://fal.run/fal-ai/bytedance/seedream/v4.5/edit` | The AI generation endpoint |
| **Env file** | `/root/aia-engine/.env` | FAL_KEY, OPENROUTER_API_KEY |

---

## The Winning Formula (Locked 2026-02-09)

### Why Seedream 4.5 Edit?
We tested Flux LoRA, SDXL img2img, and multiple other approaches. Seedream 4.5 Edit with reference conditioning is the **only pipeline** that consistently produces:
- Correct face identity (dark brown hair, hazel brown eyes, freckles)
- Correct body proportions (petite, slim, small chest)
- Character-consistent output across categories
- High-resolution output (1920x3360 auto_4K)

**Do NOT switch to any other model or endpoint.** This is the proven production pipeline.

---

## Character Identity

### General Identity (used in all prompts)
```
IDENTITY = (
    "fair skin with natural warm peach-neutral undertones, soft natural rosiness in cheeks, "
    "healthy warm fair complexion with subtle tonal variation, "
    "straight sleek dark brown hair past shoulders (dark brown NOT black, not wavy, not curly), "
    "distinctive warm olive-brown hazel eyes (NOT green, NOT grey, NOT blue), "
    "prominent visible natural freckles scattered across nose and cheeks, "
    "very petite slim narrow body frame, thin and slender with a boyish straight figure, "
    "no prominent curves anywhere, very narrow straight hips, "
    "slim athletic build like a young ballet dancer, delicate small frame, "
    "clothing hangs loosely on her thin frame"
)
```

### Reference Images (in `/root/aia-engine/content/references/starbright_monroe/advanced/`)

| File | Role | Used In |
|------|------|---------|
| `01_face_front.jpg` | Face identity anchor | Generation (ref 1), Transform (ref 1) |
| `03_eyes_freckles_enhanced.jpg` | Freckle pattern lock | Transform only (ref 2) |
| `05b_body_front_casual.jpg` | Body proportions (front) | Generation (ref 2 for front poses), Transform (ref 3) |
| `06_body_back.webp` | Body proportions (rear) | Generation (ref 2 for rear poses), Transform (ref 4) |

Also available but not primary:
- `00_canonical_face.jpg` — alternate face reference
- `03b_freckle_detail.jpg` — extreme freckle close-up
- `03_eyes_freckles.jpg` — original freckle reference
- `05a_body_front_hips.jpg` — alternate body front
- `05c_body_athletic.jpg` — athletic pose body ref

---

## NSFW Physical Specifications (Locked from v4-v9 Testing, Feb 22-23 2026)

These details were established through 9 iterative test rounds (v1-v9) and must be included in all explicit/artistic nude generation prompts for anatomical consistency. This is the definitive reference for Starbright's intimate physical characteristics.

### Breasts
- Small natural A-cup / near-flat AA-cup (NOT B-cup, NOT round, NOT perfect spheres)
- Small pink nipples with light pink areolas
- Nipples proportional to small breast size — small, slightly raised, natural coloring
- Smooth bare skin on chest with freckles scattered across upper chest and shoulders
- Visible rib structure and collarbones (shows petite frame)

### Intimate Areas
- Clean shaved smooth skin in all intimate areas
- Natural realistic vulva — anatomically accurate with visible labia contour
- Vulva naturally recessed into groin crease (NOT flat on surface — NOT Ken-doll smooth)
- Natural human contour to vaginal and anal area
- Pale ivory skin tone consistent everywhere including intimate areas
- Smooth shaved legs (no body hair anywhere)

### Body Details for Nude Content
- Very petite slim boyish straight figure like a young ballet dancer
- No prominent curves anywhere — very narrow straight hips
- Thin delicate frame with visible rib structure and collarbones
- Freckles continue from face across chest and shoulders (fade below)
- Bare feet in indoor scenes (no shoes/heels unless specified)
- No belly piercing (persistent artifact from certain pose sources — must explicitly prohibit)
- No jewelry, earrings, chokers, or accessories unless specified

### NSFW Prompt Template
When generating explicit or artistic nude content, ALWAYS include these details in the prompt:
```
small natural A-cup breasts with small pink nipples and light pink areolas clearly visible,
nipples anatomically correct — small, slightly raised, proportional to small breast size,
clean shaved smooth skin, natural realistic vulva with visible labia contour,
vulva naturally recessed into groin crease, anatomically accurate genital detail,
freckles scattered across chest and shoulders, visible rib structure and collarbones,
pale ivory skin tone consistent everywhere, smooth shaved legs,
no belly piercing, no navel piercing, no jewelry, no shoes
```

### NSFW Negative Prompt Additions
Always add to negative prompt for explicit content:
```
belly piercing, navel piercing, belly button ring, jewelry, earrings, choker, necklace,
shoes, heels, sandals, hairy legs, body hair, large breasts, B-cup, C-cup, curvy,
wide hips, thick thighs, Ken-doll smooth crotch, censored, blurred anatomy,
smoothed over body parts
```

### Known Model Tendencies to Fight
These are patterns Seedream 4.5 drifts toward that must be actively corrected:
1. **Belly piercing** — leaks from certain NSFW pose source images, must be explicitly prohibited
2. **Breast enlargement** — model tends to drift from AA to B-cup, must constrain with "flat AA-cup"
3. **Ken-doll smoothing** — safety alignment in model weights smooths intimate areas, must specify full anatomical detail
4. **Hairy legs** — occasional artifact, specify "smooth shaved"
5. **Random accessories** — shoes, heels, chokers, jewelry appear uninstructed
6. **Doll-face syndrome** — oversized eyes, glossy lips from Seedream's aesthetic bias — fight with "natural proportioned eyes, natural lips, no gloss"
7. **Hip widening** — model drifts toward curvier proportions, must specify "narrow straight hips, thin thighs with gap"

### Iteration History (for context)
| Version | Best Score | Key Wins | Remaining Issues |
|---------|-----------|----------|------------------|
| v4 | 7/10 | First correct anatomy with NSFW refs | Extra legs, deformities from pose conflict |
| v5 | 7.5/10 | No deformities, NSFW refs as pose sources | Doll face, skeletal body |
| v6 | 7/10 | Better face, iPhone selfie style | Phone frame render |
| v7 | 8/10 | Natural face, best seated pose | Mirror selfie, piercing |
| v8 | 9/10 | Playful couch near-perfect | Belly piercing, breasts slightly large |
| v9 | 9/10 | Bed spread excellent, no piercings on 3/4 | Breasts not fully flat on some |

---

## Generation Pipeline (`nsfw_pipeline_seedream.py`)

### How It Works
1. Selects prompt from category (31 total across 6 categories)
2. Builds full prompt: `CHARACTER_ANCHOR + scene_prompt + HYPERREAL_SKIN + HYPERREAL_QUALITY + CAMERA_SETTINGS`
3. Encodes 2 reference images as base64 data URIs:
   - **Ref 1**: Face front (`01_face_front.jpg`) — always included
   - **Ref 2**: Body — auto-selects `05b_body_front_casual.jpg` for front poses OR `06_body_back.webp` for rear/back poses
4. Sends to Seedream 4.5 Edit endpoint with `safety_checker: false`
5. Saves output as PNG to output directory
6. (Optional) QC check via vision model
7. (Optional) Pushes to gallery server

### Usage
```bash
# List all categories and prompts
python3 nsfw_pipeline_seedream.py --list

# Generate 1 image per category (all categories)
python3 nsfw_pipeline_seedream.py

# Generate specific categories
python3 nsfw_pipeline_seedream.py --categories explicit artistic_nude --count 2

# Skip QC check
python3 nsfw_pipeline_seedream.py --categories lingerie --count 1 --no-qc

# Don't push to gallery
python3 nsfw_pipeline_seedream.py --categories sfw_teaser --count 3 --no-push
```

### Categories (31 total prompts)
| Category | Count | Tier | Description |
|----------|-------|------|-------------|
| `lingerie` | 5 | Soft | Lingerie/underwear scenes |
| `bikini` | 4 | Soft | Swimwear/poolside |
| `artistic_nude` | 4 | Medium | Artistic nude photography |
| `explicit` | 8 | XXX | Explicit content |
| `implied_nude` | 5 | Medium | Suggestive but not fully nude |
| `sfw_teaser` | 5 | SFW | Safe-for-work teaser content |

### Anti-Detection
The pipeline includes anti-AI-detection measures in the prompt:
- Hyperrealistic skin texture (pores, imperfections, asymmetry)
- Film grain and shallow depth of field
- Natural casual pose language
- Negative prompt blocks smooth/plastic/CGI/perfect patterns

---

## Transform Pipeline (`nsfw_transform.py`)

### How It Works
1. Takes an input image (any source — downloaded, screenshot, AI-generated from another model)
2. Builds the **5-reference stack**:
   - Ref 1: Face close-up (`01_face_front.jpg`) — identity anchor
   - Ref 2: Eyes + freckles (`03_eyes_freckles_enhanced.jpg`) — detail lock
   - Ref 3: Body front (`05b_body_front_casual.jpg`) — proportions
   - Ref 4: Body back (`06_body_back.webp`) — rear angles
   - Ref 5: **The input image** — pose/outfit/setting preservation
3. All 5 images encoded as base64 data URIs in `image_urls[]`
4. Sends to same Seedream 4.5 Edit endpoint
5. Result preserves the pose/composition of the input but swaps the identity to Starbright

### Usage
```bash
# Basic transform (balanced preset)
python3 nsfw_transform.py --input /path/to/image.jpg

# Different character
python3 nsfw_transform.py --input /path/to/image.jpg --character starbright_monroe

# Strong identity application
python3 nsfw_transform.py --input /path/to/image.jpg --preset strong

# With extra prompt context
python3 nsfw_transform.py --input /path/to/image.jpg --prompt "bedroom setting, warm lighting"

# Batch transform entire directory
python3 nsfw_transform.py --input-dir /path/to/images/ --output-dir /path/to/output/

# Push result to gallery
python3 nsfw_transform.py --input /path/to/image.jpg --push-gallery

# List available presets and characters
python3 nsfw_transform.py --list-presets
python3 nsfw_transform.py --list-characters
```

### Presets
| Preset | Behavior |
|--------|----------|
| `light` | Source-dominant — preserves most of original image |
| `balanced` | Default — strong identity with good pose preservation |
| `strong` | Identity-dominant — heavy character features applied |

---

## Gallery Integration

### Push Flow
```
Generation/Transform → Output PNG → POST to localhost:8888/api/upload → Gallery review
```

### Gallery Server (port 8888)
- **Upload endpoint**: `POST http://localhost:8888/api/upload` (JSON body: `{image_data, filename, source}`)
- **Source folders scanned**: Final, Archives, Seedream, Generated, Hub, Old
- **Hub uploads land in**: `/root/aia-engine/content/hub_uploads/`
- **Review**: Approve/reject images through Hub UI or gallery directly
- **Feedback**: Reject with notes (stored in `/root/aia-engine/content/gallery_feedback.json`)

### From Hub
The Hub (Replit app) can also push images to the gallery:
- `POST /api/content-assets/:id/push-to-gallery` — push AIA Engine content
- `POST /api/chat/upload-image` — upload from chat interface
- Transform tab uploads input → transforms → auto-pushes result

---

## Environment Variables

Required in `/root/aia-engine/.env`:
```
FAL_KEY=<fal.ai API key>
OPENROUTER_API_KEY=<for QC vision checks>
```

---

## Output Naming Conventions

### Generation
```
starbright_{scene_slug}_{timestamp}.png
# Example: starbright_kneeling_couch_back_v2_20260223_024900.png
```

### Transform
```
transform_{input_hash}_{timestamp}_{short_id}.png
# Example: transform_03034e113bcac3ca0fb787f6c9e90940_33_20260223_082640_9fa3a9.png
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Wrong hair color (blonde/red) | Check that face reference is `01_face_front.jpg`, not an alternate |
| Wrong eye color | Ensure IDENTITY includes "warm olive-brown hazel eyes (NOT green, NOT grey, NOT blue)" |
| Pose not preserved in transform | The input image must be ref 5 (last in the array) |
| Gallery push fails | Check `curl http://localhost:8888/api/health` — restart gallery if down |
| FAL_KEY error | Check `/root/aia-engine/.env` has valid key |
| Low quality output | Ensure anti-detection negative prompt is included |
| Image too small | Should be auto_4K (1920x3360) — check `image_size` parameter |
| Breasts too large | Add "flat AA-cup, NOT B-cup" to prompt, add "large breasts, B-cup" to negative |
| Ken-doll smooth crotch | Add full anatomical detail language from NSFW Prompt Template above |
| Belly piercing appearing | Add "no belly piercing, no navel piercing" to both prompt and negative |
| Doll face / oversized eyes | Add "natural proportioned eyes, no gloss on lips" to prompt |
| Legs too thick / hips too wide | Add "narrow straight hips, thin thighs with gap, boyish figure" |
| Hairy legs | Add "smooth shaved legs, no body hair" to prompt |

---

## DO NOT

- **Do NOT switch to Flux, SDXL, or any other model** — Seedream 4.5 Edit is the locked production pipeline
- **Do NOT change reference image order** — the 5-ref stack order matters (face, freckles, body front, body back, source)
- **Do NOT enable safety_checker** — it blocks all NSFW content
- **Do NOT modify CHARACTER_ANCHOR** without testing — it's the identity anchor for all generations
- **Do NOT use the old `nsfw_pipeline.py`** — it's the deprecated Flux LoRA pipeline, replaced by `nsfw_pipeline_seedream.py`
- **Do NOT omit NSFW anatomical details from explicit prompts** — the model will default to Ken-doll smoothing without explicit instructions
- **Do NOT use clothed hero images as pose sources for nude content** — causes extra limb deformities from clothing-to-nude conflict. Use existing nude images as pose sources instead
