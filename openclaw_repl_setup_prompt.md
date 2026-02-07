# OpenClaw Hub — New Repl Setup Prompt

Copy everything below the line into your new Repl's agent chat:

---

## Project: OpenClaw Hub

Build a Python/FastAPI application called **OpenClaw Hub** — a personal operations platform and social media command center. This is the central hub for managing social media across all platforms, automating browser-based tasks via an OpenClaw VPS, conducting research, and serving as a general-purpose personal assistant for multiple business ventures. It connects to external services (including a separate AI content generation engine) as needed, but operates independently as its own platform.

### Architecture Overview

```
OpenClaw Hub (this Repl)
│
├── Core Platform
│   ├── Personal assistant & task management
│   ├── Multi-project/venture dashboard
│   └── Notes, reminders, and action items
│
├── Social Media Command Center
│   ├── DM management (all platforms)
│   ├── Content scheduling & posting queue
│   ├── Cross-platform analytics
│   ├── Engagement tracking & response management
│   └── Third-party scheduling platform integrations
│
├── Research & Intelligence
│   ├── SerpAPI web search skill
│   ├── Competitor analysis
│   ├── Trend tracking (hashtags, topics, market)
│   └── Business research for any venture
│
├── Browser Automation (OpenClaw VPS)
│   ├── VPS management (wake, status, tasks)
│   ├── Browser-based social media actions
│   ├── DM handling & responses
│   └── Automated posting & scheduling
│
└── External Service Integrations
    ├── AIA Engine API (AI influencer content generation — separate Repl)
    ├── Future: additional content/service APIs as ventures grow
    └── Third-party platforms (scheduling tools, analytics, etc.)
```

### Core Components to Build

**1. FastAPI Backend (port 5000)**
- Health check and system status endpoints
- Dashboard serving and API routes
- Modular router architecture — easy to add new feature areas
- Background task queue for async operations
- Database for persistent state (scheduled posts, DM history, tasks, notes)

**2. Personal Assistant Module**
This is the owner's general-purpose assistant hub:
- **Task management** — Create, track, and manage tasks across multiple projects/ventures
- **Notes & context** — Store notes, ideas, and reference material organized by project
- **Action items** — Track to-dos with due dates and priorities
- **Project tracking** — Manage multiple business ventures with separate contexts
- Design this to be extensible — new project types and workflows can be added over time

**3. Social Media Command Center**
The primary operational module for managing all social media activity:
- **DM Management** — View, track, and respond to DMs across platforms. Store conversation history in the database. Support templates for common responses.
- **Content Scheduling** — Queue content for posting at optimal times. Support multiple platforms (Twitter/X, Instagram, TikTok, Reddit, DFans). Calendar view of scheduled posts.
- **Posting Queue** — Manage a queue of content ready to post. Support draft, scheduled, posted, and failed states. Retry logic for failed posts.
- **Engagement Tracking** — Track responses, likes, comments on posted content. Flag high-priority DMs or mentions for attention.
- **Platform Accounts** — Manage credentials and connection status for each social platform.

**4. OpenClaw VPS Communication**
The VPS runs OpenClaw (browser automation agent) on a Vultr server:
- **VPS Management** — Wake, sleep, check status, send agent tasks
- **Browser Automation** — Instruct the VPS to perform browser-based actions (post content, respond to DMs, navigate platforms)
- **Task Queue** — Send structured tasks to the VPS agent and track their completion
- VPS IP and port configured via environment variables: `OPENCLAW_VPS_IP`, `OPENCLAW_VPS_PORT`
- Default VPS: 45.32.219.67:18789
- VPS webhook endpoints: `/hooks/wake`, `/hooks/agent`
- Authentication via `OPENCLAW_GATEWAY_TOKEN` (Bearer token)
- All token comparisons must use HMAC-safe constant-time comparison (`hmac.compare_digest`)

**5. AIA Engine Integration (External Service)**
The AIA Engine is a **separate Repl** that handles AI influencer content generation. OpenClaw Hub calls it via API when content is needed — it's one integration among potentially many, not the center of the system.

AIA Engine API endpoints (all require Bearer token auth via `AIA_ENGINE_API_KEY`):

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/openclaw/health | Health check |
| GET | /api/openclaw/capabilities | List available generation capabilities |
| POST | /api/openclaw/generate/image | Request AI influencer image generation (SEEDream 4.5) |
| POST | /api/openclaw/generate/caption | Request AI-generated captions (Grok-powered) |
| GET | /api/openclaw/content/list | List available generated content |
| GET | /api/openclaw/content/heroes | Get curated hero images |

Authentication: `Authorization: Bearer <AIA_ENGINE_API_KEY>`

Supported influencer personas on AIA Engine:
- **Starbright Monroe** (`starbright_monroe`) — Primary AI influencer
- **Luna Vale** (`luna_vale`) — Secondary AI influencer

**6. SerpAPI Search Skill**
Build a robust search service using SerpAPI:
- Perform Google searches and return structured results
- Research competitors, market trends, and business opportunities
- Track trending hashtags and topics across platforms
- Analyze content performance trends
- Support specialized searches: news, images, shopping, local
- Return results in clean JSON format
- Cache recent results to conserve API quota

SerpAPI docs: https://serpapi.com/search-api
- Use `serpapi` Python package or direct HTTP calls to `https://serpapi.com/search.json`
- API key is in `SERPAPI_API_KEY` environment variable
- Free tier: 100 searches/month — implement smart caching

**7. Dashboard UI**
A clean, functional web dashboard (React/TypeScript with Tailwind CSS):

- **Home/Overview** — System status (VPS, AIA Engine, API quotas), recent activity feed, quick actions
- **Social Media** — DM inbox, content calendar, posting queue, engagement metrics
- **Research** — Search interface, saved research, trend reports
- **Tasks** — Personal task manager, project boards, action items
- **VPS Control** — VPS status, send commands, view task history
- **AIA Engine** — Request content, view generated assets, browse hero images
- **Settings** — Platform connections, API status, preferences

### Database Schema (PostgreSQL)

Use Replit's built-in PostgreSQL database. Key tables:

```sql
-- Task and project management
projects (id, name, description, status, created_at, updated_at)
tasks (id, project_id, title, description, priority, status, due_date, created_at, updated_at)
notes (id, project_id, content, tags, created_at, updated_at)

-- Social media management
social_accounts (id, platform, username, display_name, status, credentials_configured, created_at)
scheduled_posts (id, social_account_id, content, media_urls, scheduled_for, status, platform, posted_at, error_message, created_at)
dm_conversations (id, social_account_id, platform, contact_name, contact_id, last_message_at, status, created_at)
dm_messages (id, conversation_id, direction, content, sent_at, read, created_at)

-- Content and distribution
content_assets (id, source, type, file_path, url, metadata, created_at)
posting_queue (id, content_asset_id, platform, status, scheduled_for, posted_at, retry_count, error_message, created_at)

-- Search and research
search_queries (id, query, source, results_count, cached_results, searched_at)
research_reports (id, project_id, title, content, sources, created_at)

-- VPS task tracking
vps_tasks (id, task_type, payload, status, sent_at, completed_at, response, error_message)
```

### Environment Variables Needed

These secrets will be provided:
- `SERPAPI_API_KEY` — SerpAPI for search capabilities
- `AIA_ENGINE_API_KEY` — Shared secret to authenticate with AIA Engine API
- `AIA_ENGINE_URL` — The deployed URL of the AIA Engine Repl
- `OPENCLAW_GATEWAY_TOKEN` — Token for authenticating with OpenClaw VPS
- `OPENCLAW_WEBHOOK_TOKEN` — Webhook verification token
- `OPENCLAW_VPS_PASSWORD` — VPS admin password

These can be set as regular environment variables:
- `OPENCLAW_VPS_IP` = `45.32.219.67`
- `OPENCLAW_VPS_PORT` = `18789`

### Security Requirements

- All API endpoints that modify data or access sensitive resources must require authentication
- Use HMAC-safe constant-time comparison (`hmac.compare_digest`) for all token verification
- Never log or expose API keys, tokens, or passwords
- All credentials must come from environment variables/secrets, never hardcoded
- Health check endpoint can be public; all data-modifying endpoints require auth
- Database credentials managed automatically by Replit's built-in PostgreSQL

### Tech Stack

- **Backend**: Python, FastAPI, Uvicorn, httpx (async HTTP client), Pydantic, SQLAlchemy or asyncpg
- **Frontend**: React, TypeScript, Tailwind CSS, shadcn/ui components
- **Database**: PostgreSQL (Replit built-in)
- **Search**: SerpAPI Python integration
- **Security**: HMAC token comparison, Bearer auth, session management

### Project Structure

```
app/
├── main.py                          # FastAPI app entry point
├── config.py                        # Pydantic settings from env vars
├── database.py                      # Database connection and models
├── services/
│   ├── aia_engine_client.py         # Client for AIA Engine API
│   ├── openclaw_vps_client.py       # Client for OpenClaw VPS
│   ├── search_service.py            # SerpAPI search skill
│   ├── social_media_service.py      # Social media management logic
│   ├── task_service.py              # Personal task/project management
│   └── scheduling_service.py        # Content scheduling logic
├── api/
│   ├── vps_routes.py                # VPS management endpoints
│   ├── search_routes.py             # Search skill endpoints
│   ├── content_routes.py            # Content & AIA Engine integration
│   ├── social_routes.py             # Social media management endpoints
│   ├── task_routes.py               # Task/project management endpoints
│   └── dashboard_routes.py          # Dashboard UI routes
├── auth/
│   └── token_auth.py                # Shared auth middleware
└── models/
    ├── project.py                   # Project/task models
    ├── social.py                    # Social media models
    ├── content.py                   # Content asset models
    └── vps.py                       # VPS task models

client/                              # React frontend
├── src/
│   ├── App.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx            # Overview/home
│   │   ├── SocialMedia.tsx          # DMs, calendar, queue
│   │   ├── Research.tsx             # Search & reports
│   │   ├── Tasks.tsx                # Project/task manager
│   │   ├── VPSControl.tsx           # VPS management
│   │   ├── AIAEngine.tsx            # Content generation requests
│   │   └── Settings.tsx             # Configuration
│   ├── components/                  # Reusable UI components
│   └── services/                    # API client functions
├── package.json
└── vite.config.ts
```

### Key Design Principles

1. **This is the command center** — It orchestrates, manages, and coordinates. It doesn't do heavy content generation itself.
2. **Service-oriented** — External services (AIA Engine, VPS, SerpAPI) are pluggable integrations. The platform works even if one is offline.
3. **Multi-venture ready** — Everything is organized by projects. AI influencer work is one project; other business ventures get their own space.
4. **Resilient** — Handle any external service being offline gracefully. Queue requests and retry. Show clear status indicators.
5. **Secure** — Every secret in env vars, HMAC token auth, no plaintext credentials anywhere.
6. **Extensible** — New integrations, platforms, and features can be added without restructuring the core.

### What Success Looks Like

1. Dashboard loads showing system health (VPS status, AIA Engine connection, API quotas)
2. Can manage tasks and notes across multiple projects/ventures
3. Can view and respond to DMs from a unified inbox
4. Can schedule and queue content for posting across platforms
5. Can perform SerpAPI searches and save research
6. Can request content generation from AIA Engine
7. Can send tasks to and monitor OpenClaw VPS
8. All endpoints properly authenticated
9. Clean error handling when any external service is unreachable
10. Database persists all state across restarts
