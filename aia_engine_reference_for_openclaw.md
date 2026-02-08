# AIA Engine — Comprehensive Reference Document

**For use by OpenClaw Hub and external integrations**
**Last Updated: February 8, 2026**

---

## What Is AIA Engine?

The AIA Engine (Autonomous AI Influencer Agent Engine) is a multi-agent content generation platform that creates hyper-realistic, photorealistic AI influencer content. It manages multiple AI personas, generates images and videos, writes captions, optimizes hashtags, and handles content workflows from creation through approval to posting.

It is deployed as a separate Replit application and exposes API endpoints for external services to request content generation.

---

## Personas / AI Influencers

### Starbright Monroe (`starbright_monroe`) — Primary
- **Identity**: 19-year-old woman, extremely pale porcelain ivory white cool-toned skin, straight sleek dark brown hair past shoulders, olive-brown eyes, natural freckles across nose and cheeks, very petite slim boyish straight figure like a young ballet dancer, delicate bony frame with no prominent curves, clothing hangs loosely on her thin frame
- **Aesthetic**: Lifestyle & wellness, confident, warm, flirty brunette model
- **Platforms**: Twitter/X (@Starbright2003), DFans (primary monetization), Instagram, TikTok
- **Voice**: Warm, personal, lightly flirty
- **Brand Tags**: #Starbright, #Fanvue

### Luna Vale (`luna_vale`) — Secondary
- **Identity**: 19-year-old woman, fair pale skin with light freckles across nose and cheeks, straight pink shoulder-length hair, blue-green eyes, slim petite build
- **Aesthetic**: Fashion & nightlife, gentle, thoughtful, quietly confident
- **Platforms**: Telegram (@LunaValeBot), DFans, Twitter/X (to be added), Instagram (to be added)
- **Voice**: Warm, calm, and intimate — speaks softly, reflects often, invites connection. Never desperate, performative, or approval-seeking.
- **Core Traits**: Gentle, thoughtful, emotionally present, quietly confident, subtle vulnerability, self-aware
- **Caption Style**: Authentic, emotionally grounded, quietly inviting. Short to medium length. Examples: "there's something about quiet mornings", "I've been thinking about this a lot lately", "tell me what's on your mind", "some moments just feel different"
- **Outfit Tiers**:
  - Tier 1 (Safe): Simple fitted cotton t-shirt, ribbed tank top, light cropped tee, oversized sweater
  - Tier 2 (Moderate): Form-fitting long sleeve top, thin strap tank top, casual lounge top, simple dress
  - Tier 3 (Bold): Off-shoulder top, fitted crop top, silky sleepwear top
- **Background Settings**: Bright neutral studio, soft beige wall with natural light, minimal bedroom, sunlit window, bedroom at golden hour, soft morning light, evening indoor lighting
- **Camera & Lighting**: Front-facing portrait or slight angle, chest-up or shoulders-up framing, soft diffused lighting, realistic shadows, shallow depth of field, Instagram-friendly composition
- **Status**: Active with modular prompt system (tiered outfits, modular backgrounds/vibes, safety guardrails, batch generation)

---

## Core Capabilities

### 1. Image Generation

**Primary: Fal.ai SEEDream 4.5 Edit Service**
- Hyper-realistic image generation with reference image conditioning
- 5-reference image transformation workflow (1 pose, 2 face, 2 body)
- Supports up to 10 reference images for maximum consistency
- 8K ultra-detailed output with natural skin texture, visible pores
- Identity descriptors enforce consistent appearance across all generations
- Guidance scale: 7.5 for revealing clothing, 9.0 for clothed
- Aspect ratio: 9:16 for full-body images

**Fallback: Replicate Seedream 4.5**
- Multi-reference generation via Replicate API
- Used when Fal.ai is unavailable

**Additional Image Services:**
- **InstantID** (Fal.ai) — Identity transfer onto different poses
- **Pose Transfer** (Fal.ai Leffa) — Preserve pose while applying new identity
- **Custom LoRA** (Fal.ai Flux/SDXL) — Custom model generation from uploaded safetensors
- **Venice AI** — Uncensored image generation with multiple models
- **Avatar Realism Pipeline** — Multi-step enhancement to reduce AI detection (skin texture, fabric texture, noise, upscaling)

### 2. Video Generation

**Micro-Movement Videos (Primary)**
- **Kling v2.1** (Replicate) — Best for face preservation and natural movements
- **ConsistI2V** — Visual consistency across frames
- **Stable Video Diffusion** — General image-to-video
- Converts hero images into short-form video loops
- Pre-defined movement types: subtle breathing, hair movement, eye blinks, gentle sway

**Talking Head Videos**
- **OmniHuman v1.5** (Fal.ai) — Lip-sync talking avatars from single image + audio
- Perfect for DFans funnel content with personalized messages
- Supports turbo mode for faster generation

**Character Replace in Video**
- **Wan-2.2** (Fal.ai) — Replace characters in existing videos while preserving scene

### 3. Caption & Text Generation

**Caption Generation**
- Platform-specific captions (Twitter, Instagram, TikTok, Reddit, DFans)
- Persona-specific tone and style (Starbright: warm/flirty, Luna: alt/cute)
- Template banks with variable substitution
- AI-powered captions via Grok (XAI)

**Hashtag Optimization**
- Context-aware hashtags via XAI/Grok
- Forbidden list: NO AI-related hashtags (#aimodel, #aigirl, #aibeauty, etc.)
- Optimized for maximum reach and engagement
- Persona-specific brand tags included

**CTA Optimization**
- Bio CTAs, pinned post CTAs, post CTAs
- Optimized for DFans/Fanvue traffic
- Grok AI-powered suggestions

### 4. Content Workflow & Management

**Content Curation**
- Quality scoring (skin realism, face consistency, lighting, composition)
- Approval/rejection workflow
- Batch scoring capability
- Vision LLM quality assessment (Grok Vision)

**Content Calendar**
- AI-generated themed weekly/monthly calendars
- Theme-based scheduling (Motivation Monday, Tease Tuesday, etc.)
- Optimal posting time suggestions

**Posting Pipeline**
- Content → Caption → Hashtags → CTA → Post Package
- Twitter/X automated posting (OAuth 2.0 text + OAuth 1.0a media)
- Reddit automated posting (PRAW)
- Manual queue for Instagram/TikTok (requires mobile posting)
- Post status tracking (draft, scheduled, posted, failed)

### 5. Research & Intelligence

**Prompt Intelligence**
- CLIP image analysis
- CogVLM image analysis
- Full multi-model image analysis
- Prompt optimization based on analysis

**Pose Analysis**
- Grok Vision-powered pose extraction from reference images
- Camera angle, lighting, and composition analysis
- Auto-generated optimized prompts from image analysis

**Hero Image Analysis**
- Auto-descriptive filename generation
- Content tag extraction
- Quality assessment

### 6. Music & Audio

- Music library management
- AI-powered track recommendation based on content context
- Trend analysis for music selection
- FFmpeg integration for merging music with video
- Track upload and organization

---

## API Endpoints Available to OpenClaw Hub

### Authentication
All endpoints (except /health and /capabilities) require Bearer token authentication:
```
Authorization: Bearer <AIA_ENGINE_API_KEY>
```

### OpenClaw Integration Endpoints (Primary)

These are the endpoints specifically designed for external service consumption:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/openclaw/health` | Health check (public) |
| GET | `/api/openclaw/capabilities` | List available capabilities (public) |
| POST | `/api/openclaw/generate/image` | Generate AI influencer image |
| POST | `/api/openclaw/generate/caption` | Generate platform-specific captions |
| GET | `/api/openclaw/content/list` | List available generated content |
| GET | `/api/openclaw/content/heroes` | Get curated hero images |
| GET | `/api/openclaw/vps/status` | Check OpenClaw VPS status |
| POST | `/api/openclaw/vps/agent` | Send task to VPS agent |
| GET | `/api/openclaw/webhook/info` | Integration documentation |

### Image Generation Request

```json
POST /api/openclaw/generate/image
{
    "influencer": "starbright_monroe",
    "content_type": "image",
    "prompt": "Professional photo in luxury bedroom, morning light, wearing silk robe",
    "style": "intimate, soft lighting, 8K detail",
    "callback_url": null
}
```

**Response:**
```json
{
    "success": true,
    "image_path": "content/seedream4_output/starbright_xxx.png",
    "prompt": "...",
    "influencer": "starbright_monroe"
}
```

### Caption Generation Request

```json
POST /api/openclaw/generate/caption
{
    "influencer": "starbright_monroe",
    "context": "morning selfie in bedroom",
    "mood": "playful",
    "platform": "twitter",
    "count": 3
}
```

**Response:**
```json
{
    "success": true,
    "influencer": "starbright_monroe",
    "platform": "twitter",
    "captions": ["caption 1...", "caption 2...", "caption 3..."],
    "count": 3
}
```

### Content Listing

```
GET /api/openclaw/content/list?influencer=starbright_monroe&content_type=image&limit=20
```

**Response:**
```json
{
    "files": [
        {
            "filename": "starbright_xxx.png",
            "path": "content/seedream4_output/starbright_xxx.png",
            "size_kb": 1234.5,
            "modified": "2026-02-07T..."
        }
    ],
    "count": 10
}
```

### Hero Images

```
GET /api/openclaw/content/heroes?influencer=starbright_monroe&limit=10
```

---

## Additional API Endpoints (Advanced)

These endpoints are available on the AIA Engine and could be exposed to OpenClaw Hub in the future as new integration points:

### Content Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/content/list/{persona}/{tier}` | List content by persona and tier |
| GET | `/api/content/stats/{persona}` | Content statistics |
| POST | `/api/content/move` | Move content between tiers |

### Identity Transfer
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/identity/transfer` | Single identity transfer |
| POST | `/api/identity/batch-transfer` | Batch identity transfer |
| POST | `/api/identity/pipeline` | Full identity pipeline |
| POST | `/api/identity/upload-and-transfer` | Upload source + transfer |

### Pose Transfer
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/pose/transfer` | Single pose transfer |
| POST | `/api/pose/batch-transfer` | Batch pose transfer |

### Micro-Loop Workflow
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/micro_loop/generate` | Generate micro-movement video |
| POST | `/micro_loop/caption` | Add caption to video |
| POST | `/micro_loop/watermark` | Add watermark to video |
| POST | `/micro_loop/upload_hero` | Upload hero image |
| GET | `/micro_loop/models` | Available video models |
| GET | `/micro_loop/movements` | Available movement types |
| GET | `/micro_loop/list` | List generated videos |
| POST | `/micro_loop/analyze_hero` | AI analysis of hero image |
| GET | `/micro_loop/generate_caption` | Generate AI caption for content |

### Content Calendar
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/generate/week` | Generate weekly content calendar |
| GET | `/api/calendar/generate/month` | Generate monthly content calendar |
| GET | `/api/calendar/today` | Get today's scheduled content |
| GET | `/api/calendar/themes` | Available content themes |

### Content Curation
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/curation/pending` | Get pending content for review |
| POST | `/api/curation/approve` | Approve content |
| POST | `/api/curation/reject` | Reject content |
| POST | `/api/curation/score` | Score single image quality |
| POST | `/api/curation/score-batch` | Score batch of images |

### CTA Optimization
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cta/bio` | Generate optimized bio CTA |
| GET | `/api/cta/post` | Generate post CTA |
| GET | `/api/cta/pinned` | Generate pinned post CTA |
| GET | `/api/cta/random` | Get random CTA from library |

### Prompt Intelligence
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/prompt-intelligence/analyze/full` | Full image analysis |
| POST | `/api/prompt-intelligence/analyze/clip` | CLIP-based analysis |
| POST | `/api/prompt-intelligence/analyze/cogvlm` | CogVLM analysis |

### Music & Audio
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/music/recommend` | AI music recommendation |
| GET | `/api/music/tracks` | List available music tracks |
| POST | `/api/music/merge` | Merge music with video |
| GET | `/api/music/trends` | Music trend analysis |

### Custom LoRA
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/lora/upload` | Upload custom LoRA model |
| POST | `/api/lora/generate` | Generate with LoRA |
| POST | `/api/lora/generate-sdxl` | Generate with SDXL LoRA |

### Twitter/X Posting (Full Integration)

AIA Engine has a complete Twitter/X integration with OAuth 2.0 + OAuth 1.0a:

**Connected Account**: @Starbright2003

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/twitter/status` | Check Twitter connection status and authorized user |
| GET | `/api/twitter/auth` | Start OAuth 2.0 authorization flow (browser redirect) |
| GET | `/api/twitter/callback` | OAuth callback handler (automatic) |
| POST | `/api/twitter/post` | Post a text-only tweet |
| POST | `/api/twitter/post-full` | Post tweet with media (image or video) |
| GET | `/api/twitter/compose` | Preview a composed post before sending |
| GET | `/api/twitter/disconnect` | Disconnect Twitter account |

**How Twitter Posting Works:**

1. **Text-only tweets** use OAuth 2.0 (scopes: tweet.read, tweet.write, users.read, offline.access)
2. **Media uploads** (images/videos) use OAuth 1.0a — Twitter requires this for media
3. The system automatically handles token refresh for long-lived sessions

**Auto-Post Flow:**
- When content is approved via `/workflow/approve?auto_post=true`, the system automatically:
  1. Generates a caption using Grok (persona-specific tone)
  2. Generates optimized hashtags (no AI tags)
  3. Generates a DFans CTA
  4. Composes the full post (caption + hashtags + CTA)
  5. Uploads the media via OAuth 1.0a
  6. Posts the tweet via OAuth 1.0a with media attached
  7. Returns the tweet URL

**Post with Media Request:**
```json
POST /api/twitter/post-full
{
    "text": "Your caption text here #hashtags",
    "media_path": "content/seedream4_output/starbright_xxx.png",
    "influencer": "starbright_monroe"
}
```

**Response:**
```json
{
    "success": true,
    "tweet_id": "1234567890",
    "tweet_url": "https://twitter.com/i/status/1234567890",
    "media_type": "image"
}
```

**Important**: OpenClaw Hub can trigger Twitter posts through AIA Engine's API — all Twitter credentials stay in AIA Engine. OpenClaw Hub does NOT need its own Twitter API keys for Starbright's account.

### Posting & Distribution (General)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workflow/auto-post` | Auto-post approved image to X with AI captions/hashtags/CTA |
| GET | `/manual_queue` | Get manual posting queue (Instagram/TikTok) |
| POST | `/manual_queue/mark_posted` | Mark item as manually posted |

### Pipeline Control
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/pipeline/run` | Run full content pipeline |
| GET | `/pipeline/status` | Check pipeline status |
| GET | `/pipeline/dry_run` | Preview pipeline without executing |

---

## Multi-Agent Architecture

The AIA Engine runs a multi-agent system coordinated by an orchestrator:

| Agent | Role |
|-------|------|
| **IdentityAgent** | Manages persona identity (name, handle, niche, voice, themes) |
| **ReferenceAgent** | Orchestrates image generation across multiple backends |
| **QualityAgent** | Assesses image quality using vision LLM |
| **ContentGenerationAgent** | Builds prompts and generates captions |
| **BackgroundAgent** | Selects scene backgrounds from reference library |
| **PoseExpressionAgent** | LLM-driven pose and expression suggestions |
| **MicroMovementAgent** | Video generation from still images |
| **CaptionAgent** | Platform-specific caption generation |
| **HashtagOptimizer** | Context-aware hashtag generation (Grok) |
| **FanvueCTAOptimizer** | CTA optimization for monetization |
| **PlannerAgent** | Daily content task planning |
| **PackagingAgent** | Creates structured post packages |
| **TwitterPosterAgent** | Automated Twitter/X posting |
| **RedditPosterAgent** | Automated Reddit posting |
| **ManualQueueAgent** | Queue for manual platform posting |
| **ContentCalendarAgent** | Themed content scheduling |
| **HeroImageAnalyzer** | Vision-based hero image analysis |
| **MusicOptimizationAgent** | Music recommendation and trends |
| **DatasetQualityAgent** | Identity consistency scoring |
| **UnifiedContentAgent** | Multi-influencer orchestration |

---

## External APIs Used by AIA Engine

These are managed internally — OpenClaw Hub does NOT need keys for these:

| API | Purpose |
|-----|---------|
| **Fal.ai** | Primary image generation (SEEDream 4.5), video (Kling), OmniHuman, pose transfer |
| **Replicate** | Fallback image generation, Kling v2.1 video, SVD |
| **XAI/Grok** | Captions, hashtags, CTAs, vision analysis |
| **Twitter API** | OAuth 2.0 posting, OAuth 1.0a media uploads |
| **Apify** | Instagram profile/post scraping |
| **Stripe** | Payment processing |

---

## Content Storage

- **Local filesystem**: `content/` directory with organized subdirectories
  - `content/seedream4_output/` — Generated images
  - `content/final/{persona}/` — Approved final content
  - `content/videos/` — Generated videos
  - `content/references/` — Reference images (face, body, background)
- **Replit Object Storage**: S3-compatible persistent cloud storage for approved assets

---

## Key Rules & Preferences

1. **No AI hashtags** — Never use #aimodel, #aigirl, #aibeauty, or similar
2. **DFans is primary monetization** — All CTAs should drive to DFans
3. **9:16 aspect ratio** for full-body images
4. **Face and body consistency** is the top priority across all images
5. **Micro-loop workflow** is the core content pipeline: Hero image → Video → Captions → Hashtags → CTA → Post
6. **Prompt safety filter** automatically transforms sensitive vocabulary to prevent content policy violations

---

## Connection Details

- **AIA Engine URL**: Set via `AIA_ENGINE_URL` environment variable
- **Authentication**: Bearer token via `AIA_ENGINE_API_KEY`
- **Protocol**: HTTPS REST API
- **Response Format**: JSON
- **Error Handling**: Returns `{"success": false, "error": "description"}` on failure
