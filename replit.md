# AIA Engine - Replit Hub Edition

## Overview
The Autonomous AI Influencer Agent Engine is a multi-agent system designed to generate hyper-realistic, photorealistic AI influencer content for multiple personas (Starbright Monroe, Luna Vale). It automates content creation, optimization, and multi-platform distribution using a "micro-loop workflow" which combines curated hero images with micro-movement video generation. The primary goal is monetization through platforms like DFans, supported by a content distribution funnel leveraging Instagram/TikTok teasers.

**Micro-Loop Workflow:** Hero image → Kling v2.1 micro-movement video → Grok captions → Grok hashtags (no AI tags) → DFans CTA → Twitter/X posting.

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
- **Image Generation**: Primary use of Fal.ai Seedream 4.5 Edit Service with reference image conditioning for character consistency and hyper-realism (e.g., specific camera specs, natural skin texture, 8K detail). This includes a prompt variation service and multi-influencer support. The system uses a 5-reference image transformation workflow (1 pose, 2 face, 2 body) for maximum control over pose and identity.
- **Multi-Agent System**: An orchestrator manages specialized agents for persona identity, video generation, content generation, captioning, optimization, scheduling, posting, and research.
- **Video/Reel Generation**: Fal.ai Kling v2.1 for image-to-video generation.
- **Content Storage**: Local filesystem (`content/`) + Replit Object Storage for persistent cloud assets.
- **Prompt Safety Filter**: Word-boundary-aware vocabulary transformation to prevent content policy violations.
- **Reference Image System**: SEEDream 4.5 supports up to 10 reference images, enabling consistent face, body, and background preservation. Identity descriptors are critical for quality, providing specific details for skin tone, hair, eyes, and body features.

### System Design Choices
- **Multi-Influencer Architecture**: Supports multiple AI influencers with isolated configurations and independent workflows.
- **Custom LoRA Support**: Fal.ai LoRA service for custom safetensor LoRA model uploads and generation.
- **Service Consolidation**: PromptSafetyFilter and PromptBuilder extracted into standalone services.
- **API Route Modularization**: Main FastAPI app split into focused routers (`admin_routes.py`, `payment_routes.py`, `micro_loop_routes.py`).
- **Python Backend**: FastAPI, Uvicorn, Pydantic.
- **React Frontend**: Vite, React, TypeScript, Tailwind CSS, shadcn/ui.
- **Object Storage**: Replit Object Storage (S3-compatible) for persistent content assets.
- **Database Migrations**: Version-tracked migrations for schema management.
- **Centralized Settings**: Pydantic for configuration management.
- **Image Generation Interface**: Abstract base class with a factory pattern to switch between SFW (Fal.ai Seedream 4.5) and potential NSFW providers.
- **Luna Modular Prompt System (V1)**: Tiered outfit system, modular background/vibe categories, safety guardrails, and batch generation with outfit consistency.

## External Dependencies

### APIs
- **Replicate API**: For Kling v2.1 (micro-movement videos) and Seedream 4.5 (image generation, as fallback).
- **XAI/Grok API**: For caption generation, hashtag optimization, and Grok Vision (image analysis).
- **Twitter API**: OAuth 1.0a (media uploads) and OAuth 2.0 (text posts).
- **Apify API**: Instagram profile/post scraping.
- **Fal.ai API**: For Seedream 4.5 hyper-realistic image generation (primary).
- **Stripe API**: For payment processing and subscription management.
- **OpenClaw VPS Integration**: Webhooks for browser automation, DM management, and social posting, with authentication via Replit Secrets.

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
- `OPENCLAW_GATEWAY_TOKEN`
- `OPENCLAW_WEBHOOK_TOKEN`
- `OPENCLAW_VPS_PASSWORD`