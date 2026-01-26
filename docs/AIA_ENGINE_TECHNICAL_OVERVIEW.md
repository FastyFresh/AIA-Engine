# AIA Engine - Technical Overview
## Autonomous AI Influencer Agent Engine

**Version:** January 2026  
**Purpose:** Multi-agent system for automated AI influencer content generation, optimization, and social media distribution

> **Business Focus (January 2026):** Primary monetization shifted from Telegram subscriptions to DFans platform. Telegram bot code preserved but inactive.

---

## 1. System Overview

The AIA Engine is an autonomous multi-agent system designed to generate hyper-realistic AI influencer content. It automates the complete content lifecycle: image generation, micro-movement video creation, AI-optimized captions/hashtags, and Twitter/X posting.

### Core Objective
Replace manual influencer content creation with an AI-driven pipeline that produces consistent, engaging, platform-optimized content at scale across multiple AI personas.

### Current Personas
| Persona | Description | Status |
|---------|-------------|--------|
| **Starbright Monroe** | Pale ivory skin, slim athletic build, long straight dark brown hair, hazel-green eyes | Primary/Active |
| **Luna Vale** | Fair pale skin with freckles, slim petite build, long pink hair, blue eyes | Configured |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND DASHBOARD                          │
│              (React + TypeScript + Tailwind + shadcn/ui)            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Monitor  │ │ Gallery  │ │ Generate │ │ Calendar │ │ Twitter  │  │
│  │   Tab    │ │   Tab    │ │   Tab    │ │   Tab    │ │   Tab    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                              │
│                    (Python + Uvicorn + httpx)                        │
├─────────────────────────────────────────────────────────────────────┤
│                         ORCHESTRATOR LAYER                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Agent Orchestrator                        │    │
│  │   Coordinates all agents for end-to-end content workflows   │    │
│  └─────────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│                           AGENT LAYER                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │   Unified    │ │    Pose/     │ │  Background  │                 │
│  │   Content    │ │  Expression  │ │    Agent     │                 │
│  │    Agent     │ │    Agent     │ │              │                 │
│  └──────────────┘ └──────────────┘ └──────────────┘                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │   Content    │ │   Caption    │ │   Hashtag    │                 │
│  │   Calendar   │ │    Agent     │ │  Optimizer   │                 │
│  │    Agent     │ │              │ │              │                 │
│  └──────────────┘ └──────────────┘ └──────────────┘                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │    DFans    │ │    Music     │ │   Twitter    │                 │
│  │     CTA     │ │  Optimizer   │ │   Poster     │                 │
│  │  Optimizer  │ │              │ │              │                 │
│  └──────────────┘ └──────────────┘ └──────────────┘                 │
├─────────────────────────────────────────────────────────────────────┤
│                          SERVICE LAYER                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │  Seedream4   │ │   Kling      │ │    Grok      │                 │
│  │   Service    │ │   Service    │ │   Client     │                 │
│  └──────────────┘ └──────────────┘ └──────────────┘                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │   Prompt     │ │  Replicate   │ │   Twitter    │                 │
│  │   Safety     │ │   Client     │ │    OAuth     │                 │
│  │   Filter     │ │              │ │              │                 │
│  └──────────────┘ └──────────────┘ └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL INTEGRATIONS                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │  Replicate   │ │   XAI/Grok   │ │  Twitter/X   │                 │
│  │     API      │ │     API      │ │     API      │                 │
│  │  (Seedream4  │ │  (Captions,  │ │  (OAuth 1.0a │                 │
│  │   Kling)     │ │  Hashtags)   │ │   + 2.0)     │                 │
│  └──────────────┘ └──────────────┘ └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Capabilities

### 3.1 Image Generation (Seedream 4.5)

**Technology:** ByteDance Seedream 4.5 via fal.ai API (Primary) / Replicate (Fallback)

**Method:** Dual/Triple Reference Image Generation
- **Face Reference:** Maintains facial identity consistency (95%+ accuracy)
- **Body Reference:** Maintains body type, skin tone, build consistency
  - Automatic back-facing reference selection for rear-angle poses
- **Background Reference:** Optional scene/environment matching

**Key Features:**
- 9:16 aspect ratio for full-body vertical content
- Prompt safety filtering with automatic vocabulary transformation
- Progressive retry logic for content policy compliance
- Pose/expression variation through LLM-powered prompt engineering

**Output:** High-resolution PNG images saved to `content/generated/{influencer_id}/`

### 3.2 Micro-Movement Video Generation (Kling v2.1)

**Technology:** Kling v2.1 via Replicate API

**Purpose:** Transform static hero images into subtle motion videos ("micro-loops")
- Adds lifelike movement to still images
- Creates engaging short-form video content
- Optimized for social media formats

### 3.3 AI-Powered Content Optimization

#### Caption Generation (Grok)
- Context-aware, persona-specific captions
- Maintains consistent voice and brand personality
- Integrates themed content requirements

#### Dynamic Hashtag Optimization (Grok)
- Time-sensitive, trend-aware hashtag generation
- **Critical Filter:** Excludes all AI-related hashtags (#aimodel, #aigirl, #aibeauty, etc.)
- Maximum reach optimization

#### CTA Optimization (Grok)
- Optimized calls-to-action for monetization (DFans is primary target)
- Bio suggestions and pinned post content
- CTA template library with rotation system
- *Note: Code references "FanvueCTAOptimizer" - legacy naming, actual target is DFans*

### 3.4 Content Calendar System

**Themed Daily Content:**
| Day | Theme | Content Style |
|-----|-------|---------------|
| Monday | Motivation Monday | Inspirational, fitness-focused |
| Tuesday | Tease Tuesday | Playful, engaging |
| Wednesday | Wellness Wednesday | Self-care, relaxation |
| Thursday | Thirsty Thursday | Bold, confident |
| Friday | DFans Friday | CTA-focused, premium |
| Saturday | Selfie Saturday | Personal, candid |
| Sunday | Soft Sunday | Intimate, cozy |

**Features:**
- Auto-scheduling optimal posting times
- Content variety suggestions
- CTA mapping per theme
- Week-ahead content planning

### 3.5 Twitter/X Posting Pipeline

**Authentication:**
- OAuth 1.0a for media uploads (images/videos)
- OAuth 2.0 for text posts

**Post Package Contents:**
- Video or image media
- AI-generated caption
- DFans CTA
- Dynamic hashtags
- Character limit handling (280 chars)

### 3.6 Prompt Safety Filter

**Purpose:** Prevent content policy violations while maintaining brand aesthetic

**Method:** Word-boundary-aware vocabulary mapping
```
lingerie → loungewear
bikini → swimwear
bra → sports top
cleavage → neckline
seductive → alluring
sensual → graceful
```

**Features:**
- Progressive retry logic on content flags
- Automatic fallback transformations
- Preserves innocent words (e.g., "celebration" not corrupted to "celeathleticstion")

---

## 4. Data Flow

```
┌─────────────────┐
│  SCHEDULING     │
│  Content        │◄──── Content Calendar Agent
│  Calendar       │       (themes, timing)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PROMPT         │
│  ASSEMBLY       │◄──── Pose/Expression Agent + Background Agent
│                 │       (LLM-powered variation)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SAFETY         │
│  FILTERING      │◄──── PromptSafetyFilter
│                 │       (vocabulary transformation)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  IMAGE          │
│  GENERATION     │◄──── Seedream4Service → Replicate API
│                 │       (face + body + background refs)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  STORAGE        │
│  content/       │
│  generated/     │───► Per-influencer directories
│  {influencer}/  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GALLERY        │
│  REVIEW         │◄──── Dashboard Gallery Tab
│                 │       (approve/reject workflow)
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│APPROVE│ │REJECT │
│       │ │       │
│content│ │content│
│/final/│ │/archive│
└───┬───┘ └───────┘
    │
    ▼
┌─────────────────┐
│  POST           │
│  OPTIMIZATION   │◄──── Caption + Hashtag + CTA Agents
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TWITTER        │
│  POSTING        │◄──── Twitter OAuth Pipeline
│                 │
└─────────────────┘
```

---

## 5. Directory Structure

```
aia-engine/
├── app/
│   ├── main.py                 # FastAPI application entry
│   ├── agents/
│   │   ├── unified_content_agent.py    # Multi-influencer orchestrator
│   │   ├── content_calendar_agent.py   # Themed scheduling
│   │   ├── pose_expression_agent.py    # LLM pose/expression selection
│   │   ├── background_agent.py         # Scene/environment selection
│   │   ├── caption_agent.py            # Caption generation
│   │   ├── hashtag_optimizer.py        # Dynamic hashtag generation
│   │   ├── fanvue_cta_optimizer.py     # CTA optimization
│   │   └── twitter_poster.py           # Twitter posting
│   └── services/
│       ├── seedream4_service.py        # Seedream4 API integration
│       ├── kling_service.py            # Kling v2.1 integration
│       ├── prompt_safety_filter.py     # Content safety filtering
│       └── grok_client.py              # XAI/Grok API client
├── client/
│   ├── src/
│   │   ├── pages/
│   │   │   └── Dashboard.tsx           # Main dashboard
│   │   └── components/
│   │       ├── gallery/
│   │       │   └── GalleryTab.tsx      # Image review/approval
│   │       ├── generate/
│   │       │   └── GenerateTab.tsx     # Manual generation
│   │       └── twitter/
│   │           └── TwitterTab.tsx      # Posting management
│   └── index.html
├── content/
│   ├── generated/
│   │   ├── starbright_monroe/          # Generated images
│   │   └── luna_vale/
│   ├── raw/                            # Source/reference images
│   ├── final/                          # Approved content
│   ├── archives/                       # Rejected content
│   ├── references/                     # Face/body reference images
│   ├── backgrounds/                    # Background reference library
│   ├── loops/                          # Micro-movement videos
│   └── post_packages/                  # Complete post bundles
└── docs/
```

---

## 6. Technology Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | FastAPI (Python) |
| Server | Uvicorn |
| HTTP Client | httpx (async) |
| Data Validation | Pydantic |
| Environment | python-dotenv |
| Twitter SDK | Tweepy |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | React 18 |
| Language | TypeScript |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| UI Components | shadcn/ui (Radix) |
| State | React Query |

### External APIs
| Service | Purpose | Authentication |
|---------|---------|----------------|
| Replicate | Seedream4, Kling v2.1 | API Token |
| XAI/Grok | Captions, Hashtags, CTAs | API Key |
| Twitter/X | Media upload, Posting | OAuth 1.0a + 2.0 |

---

## 7. API Endpoints

### Content Generation
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/generate/week` | POST | Generate full week of themed content |
| `/generate/image` | POST | Single image generation |
| `/generate/loop` | POST | Micro-movement video from image |

### Gallery Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/gallery/images/{influencer}` | GET | List images with source filtering |
| `/gallery/image/{path}` | GET | Serve image file |
| `/workflow/approve` | GET | Approve image to final |
| `/workflow/reject` | GET | Reject image to archive |

### Twitter Integration
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/twitter/post` | POST | Post content to Twitter |
| `/twitter/queue` | GET | View posting queue |

### System
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | System health check |
| `/influencers` | GET | List configured personas |
| `/logs` | GET | System logs |

---

## 8. Multi-Influencer Architecture

### Configuration
Each influencer has isolated configuration:
```python
INFLUENCERS = {
    "starbright_monroe": {
        "name": "Starbright Monroe",
        "face_ref": "content/references/starbright_face.png",
        "body_ref": "content/references/starbright_body.png",
        "description": "Pale ivory skin, slim athletic build, long dark brown hair",
        "output_dir": "content/generated/starbright_monroe/"
    },
    "luna_vale": {
        "name": "Luna Vale",
        "face_ref": "content/references/luna_face.png",
        "body_ref": "content/references/luna_body.png",
        "description": "Warm olive skin, athletic build, long dark hair",
        "output_dir": "content/generated/luna_vale/"
    }
}
```

### Isolation
- Separate reference images per persona
- Dedicated output directories
- Independent content workflows
- Persona-specific caption/hashtag generation

---

## 9. Extensibility Points

### 9.1 Adding New Personas
1. Add reference images to `content/references/`
2. Configure in INFLUENCERS dict
3. Create output directory
4. Persona ready for content generation

### 9.2 Adding New Agents
Agent interface pattern:
```python
class NewAgent:
    async def process(self, context: dict) -> dict:
        # Agent logic
        return result
```
Register in orchestrator for workflow integration.

### 9.3 Adding New Platforms
1. Create platform-specific poster agent (e.g., `instagram_poster.py`)
2. Add OAuth integration
3. Create API endpoints
4. Add dashboard tab

### 9.4 Adding New Generation Models
1. Implement `ImageGeneratorInterface` in `app/services/`
2. Register with `ImageGeneratorFactory` for content_rating routing
3. Wire into UnifiedContentAgent
4. Add safety filtering if needed

**Note:** The `ImageGeneratorInterface` (December 2024) provides an abstract base class for all image providers. Use `ImageGeneratorFactory` to get the appropriate provider based on content rating (SFW vs NSFW).

### 9.5 Content Pipeline Extensions
- **Pre-processing:** Add watermarking, branding
- **Post-processing:** Add analytics, A/B testing
- **Storage:** Add cloud storage (S3, GCS)
- **Queue:** Add Redis/Celery for async processing

---

## 10. Environment Variables

| Variable | Purpose |
|----------|---------|
| `REPLICATE_API_TOKEN` | Replicate API access |
| `XAI_API_KEY` | Grok/XAI API access |
| `TWITTER_CLIENT_ID` | Twitter OAuth 2.0 |
| `TWITTER_CLIENT_SECRET` | Twitter OAuth 2.0 |
| `TWITTER_API_KEY` | Twitter OAuth 1.0a |
| `TWITTER_API_SECRET` | Twitter OAuth 1.0a |
| `TWITTER_ACCESS_TOKEN` | Twitter posting |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter posting |
| `SESSION_SECRET` | Session management |

---

## 11. Key Design Decisions

### Why Seedream4 over LoRA Training?
- **Consistency:** 94%+ identity consistency without training
- **Speed:** Instant generation vs. hours of training
- **Flexibility:** Easy to add new personas
- **Cost:** No training compute costs

### Why Micro-Loop Workflow?
- Static images underperform on social platforms
- Subtle motion increases engagement 3-5x
- Maintains image quality while adding life

### Why Grok for Optimization?
- Strong context understanding
- Consistent brand voice maintenance
- Real-time trend awareness
- Cost-effective for high-volume generation

---

## 12. Integration Opportunities

### For Larger Systems
1. **Content Management System:** API-first design allows CMS integration
2. **Analytics Platform:** Add engagement tracking, A/B testing
3. **Multi-Platform Distribution:** Extend to Instagram, TikTok, OnlyFans
4. **Scheduling System:** Integrate with enterprise scheduling
5. **Asset Management:** Connect to DAM systems
6. **Monetization Tracking:** Link with payment/subscription platforms

### Webhook Support
Add webhook endpoints for:
- Content generation completion
- Approval workflow events
- Posting confirmations
- Analytics updates

---

## 13. Performance Characteristics

| Operation | Typical Duration |
|-----------|-----------------|
| Single image generation | 30-60 seconds |
| Week of content (7 images) | 5-7 minutes |
| Micro-loop video | 60-90 seconds |
| Caption generation | 2-3 seconds |
| Hashtag optimization | 2-3 seconds |
| Twitter post | 1-2 seconds |

---

## 14. Current Limitations

1. **Platform:** Twitter/X only (expandable)
2. **Video:** Micro-loops only, no long-form
3. **Analytics:** Basic tracking, no advanced metrics
4. **Queue:** In-memory, no persistent job queue
5. **Storage:** Local filesystem (cloud-ready architecture)

---

## 15. Prompt Variation Service

### Overview
Prevents repetitive content by automatically rotating poses, expressions, and accessories across image generations.

### Pose Catalog (Provocative)
1. Full body pose, arched back, looking over shoulder seductively
2. Full body pose, leaning forward slightly, emphasizing curves
3. Full body pose, hand on hip, confident stance
4. Full body pose, body angled with one leg forward
5. Full body side profile, accentuating figure
6. Full body pose, looking back over shoulder, body turned
7. Full body pose, sitting with legs crossed elegantly
8. Full body pose, kneeling gracefully
9. Full body pose, standing with slight hip pop
10. Full body pose, one hand touching hair

### Expression Catalog (Seductive)
1. Sultry bedroom eyes with slightly parted lips
2. Seductive smirk with knowing gaze
3. Playful teasing expression with tongue slightly visible
4. Confident direct gaze with subtle smile
5. Coy smile looking through lashes
6. Intense smoldering stare
7. Soft inviting expression with warm eyes
8. Knowing smirk with raised eyebrow
9. Dreamy half-smile with distant gaze
10. Fierce confident expression

### Outfit Enhancement
Transforms garments to be more alluring:
- skirt → short mini skirt
- dress → short tight dress
- top → revealing crop top
- bodysuit → form-fitting bodysuit hugging curves
- swimwear → revealing swimwear

### Narrative Pose Preservation
Detects specific poses in prompts and preserves them with full-body framing:
- "lying on stomach" → "full body shot from head to feet, lying on her stomach, legs extended behind"
- "sitting on bed" → "full body sitting pose showing entire figure"

---

## 16. Known Limitations

1. **Content Moderation**: Replicate's platform-level filters may flag provocative content even with disable_safety_checker enabled
2. **Negative Prompts**: Seedream4 does not support negative_prompt parameter - must use positive phrasing
3. **Agent Interruption**: Messages queue during active tool execution; cannot interrupt mid-action
4. **Platform**: Twitter/X only (expandable)
5. **Video**: Micro-loops only, no long-form
6. **Storage**: Local filesystem (cloud-ready architecture)

---

*Document updated: December 11, 2024*
*For technical consultation regarding integration with larger systems*
