# AIA Engine - Replit Hub Edition

## Overview
The Autonomous AI Influencer Agent Engine is a multi-agent system designed to generate hyper-realistic, photorealistic AI influencer content for multiple personas (Starbright Monroe, Luna Vale) under Firepie LLC. It automates content creation, optimization, and multi-platform distribution using a "micro-loop workflow" which combines curated hero images with micro-movement video generation. The primary monetization channel is DFans, with content distributed via Instagram/TikTok teasers leading to Linktree, a dedicated website, and ultimately DFans for premium content.

The core business vision is to create a scalable platform for generating high-quality, consistent AI influencer content, aiming for significant market penetration in the digital influencer space and substantial revenue through premium content subscriptions.

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
- **Micro-Loop Workflow**: Automates content generation including curated hero images, micro-movement video generation (Kling v2.1), persona-specific captions, dynamic AI-optimized hashtags, and automated Twitter/X posting.
- **Content Optimization**: Includes dynamic hashtag optimization (Grok AI), AI-powered background music selection (FFmpeg), CTA optimization (Grok AI), and AI-powered content calendar scheduling.
- **Image Generation**: Utilizes ByteDance SEEDream 4.5 via Replicate API and Fal.ai Seedream 4.5 Edit Service for hyper-realistic image generation with multi-reference image conditioning, ensuring character consistency and photorealism. This includes advanced prompt structures, detailed identity descriptors, and specific camera/quality settings (e.g., 8K ultra detailed, natural skin texture). A prompt variation service prevents repetition.
- **Multi-Agent System**: An orchestrator manages specialized agents for persona identity, video generation, content generation, captioning, optimization, scheduling, posting, and research.
- **Instagram Research Agent**: Uses Apify for scraping and Grok Vision for visual analysis to inform prompt generation.
- **Prompt Safety Filter**: Implements word-boundary-aware vocabulary transformation to comply with content policies.
- **Video Generation**: Fal.ai Kling v2.1 for image-to-video generation and Wan-2.2 Animate Replace for character replacement in videos.
- **Content Storage**: Uses local filesystem and Replit Object Storage for persistent assets.
- **Multi-Influencer Architecture**: Supports multiple AI influencers with isolated configurations and independent workflows.
- **Custom LoRA Support**: Integrates Fal.ai LoRA service for custom model uploads and generation.
- **Reference Image System**: Supports up to 10 reference images for identity consistency, including face, body, and optional background references.
- **Modular API Routes**: The FastAPI application is structured into focused routers for better organization (e.g., `admin_routes.py`, `micro_loop_routes.py`).
- **Python Backend**: Built with FastAPI, Uvicorn, and Pydantic.
- **React Frontend**: Developed with Vite, React, TypeScript, Tailwind CSS, and shadcn/ui.
- **Object Storage**: Replit Object Storage (S3-compatible) for content assets.
- **Luna Modular Prompt System (V1)**: Implements a tiered outfit system, modular background/vibe categories, and safety guardrails for batch generation with outfit consistency.

### System Design Choices
- **Detailed Identity Prompts**: Emphasizes the use of highly detailed identity prompts for superior image quality and consistency, especially for Starbright Monroe.
- **Service Hierarchy**: `app/services/fal_seedream_service.py` is the primary image generation service (Fal.ai, faster/cheaper), with `app/services/seedream4_service.py` (Replicate) as a fallback for multi-reference support.
- **Prompt Builder Service**: Centralizes identity descriptions, camera settings, and hyper-realism settings.

## External Dependencies

### APIs
- **Replicate API**: For Kling v2.1 (micro-movement videos) and Seedream 4.5 (image generation).
- **XAI/Grok API**: For caption generation, hashtag optimization, and Grok Vision (image analysis).
- **Twitter API**: For OAuth 1.0a (media uploads) and OAuth 2.0 (text posts).
- **Apify API**: For Instagram profile/post scraping.
- **Fal.ai API**: For Seedream 4.5 hyper-realistic image generation.
- **Stripe API**: For payment processing and subscription management.

### Core Technologies
- **Backend**: Python (FastAPI, Uvicorn, Pydantic, httpx, python-dotenv, Tweepy).
- **Frontend**: Node.js ecosystem (Vite, React, TypeScript, Tailwind CSS, shadcn/ui).

### External Integrations
- **OpenClaw VPS Integration**: Connects AIA Engine (Replit) with an OpenClaw instance on a Vultr VPS (Ubuntu 22.04 x64) for browser automation, DM management, and social posting via webhooks. This integration is crucial for social media interaction beyond content generation.