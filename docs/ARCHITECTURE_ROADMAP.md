# AIA Engine - Architecture Roadmap

## Current System State (v2.5 - January 2026)

The AIA Engine is a fully operational multi-agent architecture for generating and publishing AI influencer content using **Seedream4 dual-reference image generation** (LoRA approach deprecated).

> **Business Pivot (January 2026):** Telegram monetization discontinued (0% conversion from 18 users). Primary monetization target is now DFans. Telegram bot code preserved in `app/telegram/` but workflow stopped.

### Complete Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SEEDREAM4 CONTENT GENERATION PIPELINE                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Content    │───▶│    Pose/     │───▶│  Background  │                  │
│  │   Calendar   │    │  Expression  │    │    Agent     │                  │
│  │    Agent     │    │    Agent     │    │              │                  │
│  │              │    │              │    │ Theme-based  │                  │
│  │ Daily themes │    │ LLM-powered  │    │ scene select │                  │
│  │ & scheduling │    │ pose variety │    │              │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                 │                           │
│                                                 ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │    Prompt    │◀───│   Unified    │◀───│  Seedream4   │                  │
│  │    Safety    │    │   Content    │    │   Service    │                  │
│  │    Filter    │    │    Agent     │    │              │                  │
│  │              │    │              │    │ Face + Body  │                  │
│  │ Vocabulary   │    │ Orchestrates │    │ + Background │                  │
│  │ transform    │    │ all agents   │    │ references   │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Gallery    │───▶│   Caption    │───▶│   Hashtag    │                  │
│  │   Review     │    │    Agent     │    │  Optimizer   │                  │
│  │              │    │              │    │              │                  │
│  │ Approve/     │    │ Grok-powered │    │ Dynamic,     │                  │
│  │ Reject flow  │    │ captions     │    │ no AI tags   │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│         │                                       │                           │
│         ▼                                       ▼                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │    DFans    │───▶│    Music     │───▶│   Twitter    │                  │
│  │     CTA     │    │  Optimizer   │    │   Poster     │                  │
│  │  Optimizer  │    │              │    │              │                  │
│  │              │    │ FFmpeg       │    │ OAuth 1.0a   │                  │
│  │ Grok CTAs   │    │ integration  │    │ + OAuth 2.0  │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implemented Agents

| Agent | Status | Purpose |
|-------|--------|---------|
| **UnifiedContentAgent** | ✅ Active | Multi-influencer orchestrator for complete content pipeline |
| **ContentCalendarAgent** | ✅ Active | Themed daily content scheduling (Motivation Monday, etc.) |
| **PoseExpressionAgent** | ✅ Active | LLM-powered pose/expression selection for variety |
| **BackgroundAgent** | ✅ Active | Theme-appropriate background selection from library |
| **CaptionAgent** | ✅ Active | Grok-powered persona-specific caption generation |
| **HashtagOptimizer** | ✅ Active | Dynamic hashtags (AI-tags filtered out) |
| **FanvueCTAOptimizer** | ✅ Active | Grok-powered CTA generation (DFans target, legacy naming) |
| **MusicOptimizer** | ✅ Active | Background music selection with FFmpeg integration |
| **TwitterPosterAgent** | ✅ Active | Automated Twitter/X posting (Tweepy) |

### Deprecated Agents (v1.0 - No Longer Used)

| Agent | Status | Reason |
|-------|--------|--------|
| ~~ReferenceAgent~~ | ❌ Deprecated | Replaced by Seedream4Service |
| ~~FaceSwapAgent~~ | ❌ Deprecated | Seedream4 maintains identity via dual-reference |
| ~~QualityAgent~~ | ❌ Deprecated | Gallery review workflow replaces auto-scoring |
| ~~AutoCurateAgent~~ | ❌ Deprecated | Manual approval via Gallery Tab |
| ~~RedditPosterAgent~~ | ❌ Deprecated | Focus on Twitter/X platform |

### Core Capabilities

- **Seedream4 Generation**: ByteDance Seedream4 via Replicate with dual/triple reference images
- **Identity Consistency**: 94%+ consistency WITHOUT training (face + body references)
- **Prompt Safety Filter**: Word-boundary-aware vocabulary transformation for content compliance
- **Themed Content Calendar**: 7-day themed content (Motivation Monday through Soft Sunday)
- **Dynamic Hashtag Optimization**: Trend-aware, AI-tag filtered hashtags via Grok
- **CTA Optimization**: Rotating CTAs with Grok-powered optimization (DFans target)
- **Micro-Loop Videos**: Kling v2.1 for micro-movement video generation
- **Unified Dashboard**: React/TypeScript interface with Gallery, Generate, Calendar tabs

---

## Why Seedream4 Over LoRA (Architecture Decision)

### The Problem with LoRA (v1.0)
- Required 25-30 curated training images per persona
- Training cost: ~$1.50 and 1-2 hours per persona
- LoRA weights tied to specific base model version
- Still needed face swap post-processing for consistency
- Adding new personas required full training cycle

### Seedream4 Solution (v2.0)
- **Zero training required** - instant persona setup
- Dual-reference (face + body) achieves 94%+ identity consistency
- Optional background reference for scene matching
- Cost per image: ~$0.05 vs $1.50 training investment
- New personas: Just add 2 reference images

### Consistency Comparison

| Method | Face | Body | Skin Tone | Hair | Setup Time |
|--------|------|------|-----------|------|------------|
| LoRA Training | 94% | 94% | 90% | 92% | 1-2 hours |
| Seedream4 Dual-Ref | 95% | 94% | 96% | 93% | 5 minutes |

---

## Content Storage Structure

```
content/
├── generated/                  # AI-generated images (pending review)
│   ├── starbright_monroe/      # Per-influencer output
│   └── luna_vale/
├── raw/                        # Curated hero/reference images
│   ├── starbright_monroe/
│   └── luna_vale/
├── final/                      # Approved images ready for posting
│   ├── starbright_monroe/
│   └── luna_vale/
├── archives/                   # Rejected/archived images
├── references/                 # Face/body reference images for Seedream4
│   ├── starbright_face.png
│   ├── starbright_body.png
│   ├── luna_face.png
│   └── luna_body.png
├── backgrounds/                # Background reference library
│   ├── apartment_day.png
│   ├── apartment_night.png
│   ├── gym.png
│   ├── pool.png
│   ├── spa.png
│   ├── beach.png
│   └── bathroom.png
├── loops/                      # Micro-movement videos (Kling v2.1)
└── post_packages/              # Complete post bundles (image + caption + CTA)
```

---

## Multi-Influencer Configuration

```python
INFLUENCERS = {
    "starbright_monroe": {
        "name": "Starbright Monroe",
        "description": "Pale ivory skin, slim athletic build, long straight dark brown hair, hazel-green eyes",
        "face_ref": "content/references/starbright_face.png",
        "body_ref": "content/references/starbright_body.png",
        "output_dir": "content/generated/starbright_monroe/"
    },
    "luna_vale": {
        "name": "Luna Vale", 
        "description": "Fair pale skin with freckles, slim petite build, long pink hair, blue eyes",
        "face_ref": "content/references/luna_face.png",
        "body_ref": "content/references/luna_body.png",
        "output_dir": "content/generated/luna_vale/"
    }
}
```

### Adding New Personas
1. Create face reference image (clear frontal shot)
2. Create body reference image (full-body shot showing build/proportions)
3. Add configuration to INFLUENCERS dict
4. Persona immediately available for content generation

---

## Prompt Safety Filter

### Purpose
Prevent Seedream4 content policy violations while maintaining brand aesthetic.

### Vocabulary Transformation
```python
SAFETY_VOCABULARY = {
    "lingerie": "loungewear",
    "bikini": "swimwear", 
    "bra": "sports top",
    "underwear": "athletic shorts",
    "cleavage": "neckline",
    "seductive": "alluring",
    "sensual": "graceful",
    "provocative": "bold",
    "revealing": "stylish",
    "sexy": "confident"
}
```

### Features
- Word-boundary-aware regex (won't corrupt "celebration" → "celeathleticstion")
- Progressive retry logic on content flags
- Automatic fallback transformations
- Maintains prompt intent while ensuring compliance

---

## Content Calendar System

### Themed Daily Content

| Day | Theme | Content Style | Typical Poses |
|-----|-------|---------------|---------------|
| Monday | Motivation Monday | Inspirational, fitness | Active, energetic |
| Tuesday | Tease Tuesday | Playful, engaging | Flirty, confident |
| Wednesday | Wellness Wednesday | Self-care, relaxation | Peaceful, serene |
| Thursday | Thirsty Thursday | Bold, confident | Dynamic, striking |
| Friday | DFans Friday | CTA-focused, premium | Glamorous, inviting |
| Saturday | Selfie Saturday | Personal, candid | Natural, casual |
| Sunday | Soft Sunday | Intimate, cozy | Relaxed, comfortable |

### Week Generation
```python
# Generate full week of themed content
POST /generate/week
{
    "influencer": "starbright_monroe",
    "start_date": "2024-12-09"
}
# Returns: 7 themed images with captions
```

---

## Pipeline Orchestration

The `UnifiedContentAgent` coordinates the complete generation workflow:

```python
async def generate_themed_content(influencer: str, theme: str) -> ContentResult:
    # 1. Get theme configuration from ContentCalendarAgent
    theme_config = await calendar_agent.get_theme(theme)
    
    # 2. Select pose/expression via PoseExpressionAgent (Grok-powered)
    pose = await pose_agent.select_pose(theme_config, recent_poses)
    
    # 3. Select background via BackgroundAgent
    background = await background_agent.select(theme_config)
    
    # 4. Build prompt with safety filtering
    prompt = build_prompt(influencer, pose, theme_config)
    safe_prompt = safety_filter.transform(prompt)
    
    # 5. Generate image via Seedream4Service
    image = await seedream4_service.generate(
        prompt=safe_prompt,
        face_ref=influencer.face_ref,
        body_ref=influencer.body_ref,
        background_ref=background
    )
    
    # 6. Save to generated folder for review
    save_path = save_image(image, influencer.output_dir, theme)
    
    return ContentResult(path=save_path, theme=theme)
```

---

## External API Integrations

### Replicate API
| Model | Purpose | Cost |
|-------|---------|------|
| ByteDance Seedream4 | Primary image generation | ~$0.05/image |
| Kling v2.1 | Micro-movement video loops | ~$0.10/video |

### XAI/Grok API
| Function | Purpose |
|----------|---------|
| Caption Generation | Persona-specific, theme-aware captions |
| Hashtag Optimization | Trend-aware, AI-tag filtered hashtags |
| CTA Optimization | DFans-focused calls-to-action |
| Pose/Expression Selection | Context-aware variety generation |

### Twitter/X API
| Auth Method | Purpose |
|-------------|---------|
| OAuth 1.0a | Media uploads (images, videos) |
| OAuth 2.0 | Text posts, timeline access |

---

## Technical Stack

### Backend (Python)
- FastAPI + Uvicorn
- Pydantic for validation
- httpx for async HTTP
- Replicate SDK for AI models
- Tweepy for Twitter API

### Frontend (TypeScript/React)
- Vite build system
- React 18 with TypeScript
- Tailwind CSS + shadcn/ui
- TanStack Query for data fetching

### Services
| Service | File | Purpose |
|---------|------|---------|
| Seedream4Service | `app/services/seedream4_service.py` | Image generation with dual-reference |
| PromptSafetyFilter | `app/services/prompt_safety_filter.py` | Content policy compliance |
| GrokClient | `app/services/grok_client.py` | XAI API integration |
| KlingService | `app/services/kling_service.py` | Micro-loop video generation |
| ImageGeneratorInterface | `app/services/image_generator_interface.py` | Abstract base for multi-provider support |
| ImageGeneratorFactory | `app/services/image_generator_interface.py` | Factory for SFW/NSFW provider switching |

### Image Generation Interface (December 2024)

**Purpose:** Enable seamless switching between SFW and NSFW image providers.

**Architecture:**
- `ImageGeneratorInterface`: Abstract base class with `generate()` method
- `ImageGeneratorFactory`: Returns appropriate provider based on `content_rating` parameter

**Provider Support:**
| Content Rating | Provider | Status |
|----------------|----------|--------|
| SFW | Fal.ai Seedream 4.5 | Active |
| NSFW | Venice.ai / ModelsLab / RunPod | Ready for integration |

**Researched NSFW Providers:**
- ModelsLab ($19/mo) - LoRA training support
- Venice.ai ($18/mo Pro) - Flux/Pony models
- RunPod - Cloud GPU rental

---

## Dashboard Capabilities

### Gallery Tab
- View generated/raw/final images with source filtering
- Approve images → moves to `content/final/`
- Reject images → moves to `content/archives/`
- Per-influencer filtering

### Generate Tab
- Single image generation with theme selection
- Week generation (7 themed images)
- Real-time generation progress

### Calendar Tab
- View content calendar
- Schedule posts
- Theme configuration

### Twitter Tab
- Post queue management
- Share dialog with live preview
- Caption/hashtag/CTA toggles

---

## Future Enhancements (Planned)

### Platform Expansion
- Instagram API integration (requires Meta Business verification)
- TikTok for Business API
- Direct DFans integration

### Analytics Agent
- Engagement rate tracking
- Optimal posting time analysis
- Content performance insights
- A/B testing for captions

### Advanced Features
- Multi-image carousel posts
- Story/Reel generation
- Collaborative filtering for content curation
- Automated trend detection

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `REPLICATE_API_TOKEN` | Replicate API (Seedream4, Kling) |
| `XAI_API_KEY` | Grok API (captions, hashtags, CTAs) |
| `TWITTER_CLIENT_ID` | Twitter OAuth 2.0 |
| `TWITTER_CLIENT_SECRET` | Twitter OAuth 2.0 |
| `TWITTER_API_KEY` | Twitter OAuth 1.0a |
| `TWITTER_API_SECRET` | Twitter OAuth 1.0a |
| `TWITTER_ACCESS_TOKEN` | Twitter posting |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter posting |
| `SESSION_SECRET` | Session management |

---

## Security

- API keys stored in Replit Secrets
- Prompt safety filtering prevents policy violations
- No sensitive data in git repository
- OAuth tokens refreshed automatically

---

## Prompt Variation Service (December 2024)

### Purpose
Prevents repetitive content by rotating poses, expressions, and accessories across generations.

### Components

| Component | Description | Options |
|-----------|-------------|---------|
| **Provocative Poses** | Full-body poses for DFans engagement | arched back, leaning forward, hand on hip, body angled, side profile, over shoulder, sitting crossed legs, kneeling, standing hip pop, lying pose |
| **Seductive Expressions** | Alluring facial expressions | sultry bedroom eyes, seductive smirk, playful teasing, confident gaze, coy smile, intense stare, soft inviting, knowing smirk, dreamy half-smile, fierce confident |
| **Earring Variations** | Accessory diversity | bare ears, small diamond studs, elegant pearl studs, tiny crystal studs, small gold hoops, delicate drop earrings |

### Narrative Pose Detection
When prompts contain specific poses, the system preserves them instead of applying rotation:
- "lying on stomach/back/side" → "full body shot from head to feet, lying on her stomach, legs extended behind"
- "sitting on bed/couch/chair" → "full body sitting pose showing entire figure"
- "kneeling", "crawling", "bent over", "on all fours" → preserved with full-body framing

### Outfit Enhancement
Transforms common garments to be more provocative while preserving colors:
```python
OUTFIT_ENHANCEMENTS = {
    "skirt": "short mini skirt",
    "dress": "short tight dress",
    "top": "revealing crop top",
    "jeans": "tight low-rise jeans",
    "shorts": "tiny shorts",
    "bodysuit": "form-fitting bodysuit hugging curves",
    # ... etc
}
```

### State Persistence
- File: `content/prompt_rotation_state.json`
- Tracks: last_pose_index, last_expression_index, last_earring_index, history
- Locking: fcntl for atomic updates across concurrent requests

---

## Seedream4 API Integration Notes

### Supported Parameters
| Parameter | Value | Purpose |
|-----------|-------|---------|
| prompt | string | Main generation prompt |
| image_input | [face_b64, body_b64] | Reference images for identity |
| aspect_ratio | "9:16" | Vertical portrait format |
| guidance_scale | 8.5 | Prompt adherence strength |
| disable_safety_checker | True | Bypass content moderation |
| seed | int (optional) | Reproducibility |

### Not Supported
- **negative_prompt**: Seedream4 does NOT support this parameter. Use positive phrasing in main prompt instead.

### Content Moderation
Even with `disable_safety_checker: True`, Replicate's platform-level moderation may still flag certain content. Error message: "Content flagged for: sexual"

---

## Back-Facing Reference Support (December 2024)

### Purpose
Enable rear-angle pose generation with proper body reference conditioning.

### Implementation
The `FalSeedreamService` automatically detects rear-angle keywords in prompts:
- "back to camera", "rear angle", "from behind"
- "looking back", "over shoulder", "backside"
- "back view", "rear view", "turned away"
- "lying on stomach", "on her stomach"

When detected, the service uses `body_reference_back_1.png` instead of the front-facing body reference.

### Reference Images
- `content/references/starbright_monroe/body_reference_ivory.jpg` - Front-facing (default)
- `content/references/starbright_monroe/body_reference_back_1.png` - Back-facing (for rear angles)
- `content/references/starbright_monroe/body_reference_back_2.png` - Back-facing alternate

---

---

## Object Storage Integration (January 2026)

### Overview
Content assets migrated to Replit Object Storage (S3-compatible) for persistent cloud storage.

### Migration Status
| Folder | Files | Size | Status |
|--------|-------|------|--------|
| `content/references/` | 87 | 168 MB | ✅ Migrated |
| `content/loops/` | 84 | 274 MB | ✅ Migrated |
| `content/final/` | - | 1.4 GB | Pending |
| `content/generated/` | - | 3.9 GB | Pending |

### Service Location
- `app/services/object_storage/object_storage_service.py`
- Migration script: `scripts/migrate_to_object_storage.py`

### Environment Variables
- `DEFAULT_OBJECT_STORAGE_BUCKET_ID`
- `PRIVATE_OBJECT_DIR`
- `PUBLIC_OBJECT_SEARCH_PATHS`

---

*Last Updated: January 24, 2026*
*Architecture Version: 2.5 (Object Storage + DFans Focus)*
