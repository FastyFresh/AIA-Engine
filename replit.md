# AIA Engine - Replit Hub Edition

*Last Updated: January 24, 2026*

## Overview
The Autonomous AI Influencer Agent Engine is a multi-agent system designed to generate hyper-realistic, photorealistic AI influencer content for multiple personas (Starbright Monroe, Luna Vale) under Firepie LLC. It automates content creation, optimization, and multi-platform distribution using a "micro-loop workflow" which combines curated hero images with micro-movement video generation.

**Primary Monetization:** DFans (dfans.co/starbrightnight)
**Content Distribution Funnel:** Instagram/TikTok (teasers) → Bio Link → Linktree → starbrightnights.com → DFans (premium)
**Status:** Telegram monetization deprecated (0% conversion from 18 users)

### Micro-Loop Workflow (Complete)
Hero image → Kling v2.1 micro-movement video → Grok captions → Grok hashtags (no AI tags) → DFans CTA → Twitter/X posting

### Pose Transfer Workflow (Jan 24, 2026 - PRODUCTION READY)

**Endpoint:** `POST /api/seedream4/generate`
**Documentation:** `docs/SEEDREAM4_POSE_TRANSFER_WORKFLOW.md`

**Proven Prompt Structure:**
```
[POSE + SETTING], [OUTFIT], [IDENTITY DESCRIPTORS], [CAMERA ANGLE], [LIGHTING], [EXPRESSION]
```

**Identity Descriptors (ALWAYS INCLUDE):**
```
very pale porcelain ivory white skin with natural freckles across nose and cheeks,
straight sleek dark brown hair, warm olive-brown eyes,
extremely thin slender petite body with very narrow tiny waist,
slim narrow hips, long thin slender legs
```

**Settings:**
- Aspect ratio: `3:4` (portrait)
- Provider: Replicate Seedream 4.5

**Success Rate:** 75% (9/12 images) - Some lingerie prompts flagged
**Key Insight:** Match camera angle from reference image exactly

**References:**
- Face reference: `content/references/starbright_monroe/starbright_face_reference_v2.png`
- Alluring pose library: `content/prompt_templates/alluring_pose_library.json`

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

**Starbright (HIGH QUALITY - 5x more detail):**
```
"very pale porcelain ivory white skin, straight sleek dark brown hair (not wavy, not curly), 
warm olive-brown eyes, natural freckles across nose and cheeks, extremely thin slender petite 
body with very narrow tiny waist, slim narrow hips, long thin slender legs, delicate small frame, 
size 0 figure"
```

**Luna (LOWER QUALITY - too vague):**
```
"young woman with long straight pink hair, blue-green eyes, slim petite figure, natural beauty, 
confident expression"
```

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