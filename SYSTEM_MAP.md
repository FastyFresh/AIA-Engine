# AIA Engine - System Map

*Last Updated: January 24, 2026*

## Entry Points

| Entry Point | Command | Purpose | Status |
|-------------|---------|---------|--------|
| **FastAPI Server** | `uvicorn app.main:app --host 0.0.0.0 --port 5000` | Main API server, dashboard, webhooks | Active |
| ~~Telegram Bots~~ | ~~`python -m app.telegram.run_bots`~~ | ~~AI influencer chat bots~~ | Deprecated |

## Application Startup Flow

### FastAPI Server (app/main.py)
1. FastAPI app initializes with CORS middleware
2. Content directories created (`content/generated`, `content/loops`, etc.)
3. Orchestrator, ContentService, ReplicateClient, MicroMovementAgent instantiated
4. Routes registered (content_admin_router)
5. Static files served from `dist/public` for React dashboard
6. Server binds to port 5000

### Telegram Bots (DEPRECATED - January 2026)
> **Note:** Telegram monetization discontinued due to 0% conversion rate (18 users, 0 paid). Code remains in `app/telegram/` but workflow is stopped. Primary monetization focus shifted to DFans.

~~1. Two InfluencerBot instances created (Starbright Monroe, Luna Vale)~~
~~2. Each bot initializes database, conversation engine, payment handler~~
~~3. Bots poll Telegram API~~

## Scheduling & Automation

| Mechanism | Trigger | Action | Status |
|-----------|---------|--------|--------|
| **Daily Cycle** | Manual via `/daily_cycle` endpoint or dashboard button | Generate batch content for influencers | Active |
| ~~Drip Onboarding~~ | ~~Admin API call to `/api/telegram/run-onboarding`~~ | ~~Send scheduled messages to free users~~ | Deprecated |
| ~~Content Drops~~ | ~~Admin API call to `/api/telegram/send-content-drop`~~ | ~~Distribute exclusive content to subscribers~~ | Deprecated |
| ~~Churn Prevention~~ | ~~Webhook on subscription.deleted~~ | ~~Auto-send win-back messages~~ | Deprecated |

*Note: No cron/scheduler daemon - automation triggered via API calls or manual dashboard actions.*

## External Services

| Service | Purpose | Integration Point | Status |
|---------|---------|-------------------|--------|
| **Fal.ai** | Image generation (Seedream 4.5), video (Kling v2.1) | app/services/fal_seedream_service.py, fal_video_service.py | Active |
| **Replicate** | Backup image/video generation | app/tools/replicate_client.py | Active |
| **Twitter/X API** | Social media posting | app/agents/twitter_poster_agent.py, twitter_oauth2_agent.py | Active |
| **Stripe** | Payment processing | app/services/stripe_client.py | Active |
| **Apify** | Instagram scraping for research | app/agents/instagram_research_agent.py | Active |
| **Replit Object Storage** | Cloud storage for content assets | app/services/object_storage/ | Active |
| ~~Telegram Bot API~~ | ~~Chat interactions, content delivery~~ | ~~app/telegram/bot_handler.py~~ | Deprecated |
| ~~OpenRouter/XAI~~ | ~~AI conversation generation~~ | ~~app/telegram/conversation_engine.py~~ | Deprecated |

## Webhooks

| Endpoint | Source | Purpose |
|----------|--------|---------|
| `POST /api/stripe/webhook` | Stripe | Payment confirmations |

### Stripe Webhook Events Handled:
- `checkout.session.completed` → Payment confirmation

## State Storage

| Type | Location | Purpose | Status |
|------|----------|---------|--------|
| **Content Metadata** | JSON files (`approval_status.json`, `pose_history.json`) | Image approval status, generation history | Active |
| **Tuning Profiles** | JSON (`tuning_profiles/*.json`) | Per-influencer generation parameters | Active |
| **Generated Content** | File system (`content/`) + Object Storage | Images, videos, references | Active |
| **Music Library** | JSON + files (`content/music/`) | Background music for videos | Active |
| **Research Cache** | JSON (`content/research_cache/`) | Competitor analysis data | Active |
| **Object Storage** | Replit Object Storage (S3-compatible) | Cloud-hosted content assets (references, loops) | Active |
| ~~User State~~ | ~~SQLite (`telegram_users.db`)~~ | ~~Telegram users, subscriptions~~ | Deprecated |

## Content Generation Flow

```
Admin triggers Daily Cycle or Manual Generation
    ↓
Orchestrator selects influencer + theme
    ↓
PoseExpressionAgent selects pose (LLM-powered)
    ↓
PromptBuilder constructs hyper-realistic prompt
    ↓
PromptSafetyFilter transforms vocabulary
    ↓
FalSeedreamService generates image with references
    ↓
Image saved to content/generated/{influencer}/
    ↓
Dashboard Gallery shows for approval
    ↓
Approved → content/final/ → Ready for posting
```

## Directory Structure

```
app/
├── main.py              # FastAPI entry point
├── orchestrator.py      # Content generation orchestrator
├── agents/              # Specialized AI agents
├── services/            # Image/video generation services
│   └── object_storage/  # Replit Object Storage integration
├── telegram/            # [DEPRECATED] Telegram bot system
├── tools/               # API clients (Replicate, Grok, LLM)
└── routes/              # Additional API routers

client/                  # React dashboard (Vite + TypeScript)
content/                 # Generated content storage (+ Object Storage)
config/                  # Configuration files
dist/public/             # Built frontend assets
```
