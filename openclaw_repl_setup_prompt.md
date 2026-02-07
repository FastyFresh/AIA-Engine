# OpenClaw Hub — New Repl Setup Prompt

Copy everything below the line into your new Repl's agent chat:

---

## Project: OpenClaw Hub

Build a Python/FastAPI application called **OpenClaw Hub** — a lightweight command-and-control bridge between an OpenClaw VPS (browser automation agent) and a remote AIA Engine (AI influencer content generation). This Repl handles VPS communication, search/research capabilities, content distribution automation, and DM management. It does NOT generate content itself — it requests content from the AIA Engine API.

### Architecture Overview

```
OpenClaw Hub (this Repl)
├── Talks to: OpenClaw VPS (Vultr Atlanta, browser automation)
├── Talks to: AIA Engine API (separate Repl, content generation)
├── Has: SerpAPI search skill (research, trends, competitor analysis)
├── Has: VPS management (status, agent tasks, wake/sleep)
└── Has: Content distribution logic (scheduling, posting queue)
```

### Core Components to Build

**1. FastAPI Backend (port 5000)**
- Health check and dashboard endpoints
- VPS communication routes (proxy to OpenClaw VPS)
- AIA Engine API client (request content generation from remote AIA Engine)
- Search skill using SerpAPI
- Content distribution queue management

**2. AIA Engine API Client**
The AIA Engine is a separate Repl that handles all content generation. This Repl communicates with it via authenticated API calls. The AIA Engine exposes these endpoints (all require Bearer token auth):

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /api/openclaw/health | Health check |
| GET | /api/openclaw/capabilities | List available generation capabilities |
| POST | /api/openclaw/generate/image | Request AI influencer image generation (SEEDream 4.5) |
| POST | /api/openclaw/generate/caption | Request AI-generated captions (Grok) |
| GET | /api/openclaw/content/list | List available generated content |
| GET | /api/openclaw/content/heroes | Get curated hero images |
| GET | /api/openclaw/vps/status | Check VPS status via AIA Engine |
| POST | /api/openclaw/vps/agent | Send agent task to VPS via AIA Engine |

Authentication to AIA Engine: `Authorization: Bearer <AIA_ENGINE_API_KEY>`

**3. OpenClaw VPS Communication**
- VPS IP and port are configured via environment variables: `OPENCLAW_VPS_IP`, `OPENCLAW_VPS_PORT`
- Default VPS: 45.32.219.67:18789
- VPS webhook endpoints: `/hooks/wake`, `/hooks/agent`
- Authentication via `OPENCLAW_GATEWAY_TOKEN` (Bearer token)
- All token comparisons must use HMAC-safe constant-time comparison

**4. SerpAPI Search Skill**
Build a search service using SerpAPI that can:
- Perform Google searches and return structured results
- Research competitor influencer accounts
- Track trending hashtags and topics
- Analyze content performance trends
- Return results in a clean JSON format suitable for AI agent consumption

SerpAPI docs: https://serpapi.com/search-api
- Use `serpapi` Python package or direct HTTP calls to `https://serpapi.com/search.json`
- API key is in `SERPAPI_API_KEY` environment variable
- Free tier: 100 searches/month

**5. Dashboard UI (simple)**
A minimal web dashboard showing:
- VPS online/offline status
- AIA Engine connection status
- Recent search queries
- Content distribution queue
- Quick action buttons (wake VPS, run search, request content)

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
- Health check endpoint can be public, all others require auth

### Tech Stack

- **Backend**: Python, FastAPI, Uvicorn, httpx (async HTTP client), Pydantic
- **Frontend**: Simple HTML/CSS/JS dashboard (no React needed — keep it lightweight)
- **Search**: SerpAPI Python integration
- **Security**: HMAC token comparison, Bearer auth

### Project Structure

```
app/
├── main.py                    # FastAPI app entry point
├── config.py                  # Pydantic settings from env vars
├── services/
│   ├── aia_engine_client.py   # Client for AIA Engine API
│   ├── openclaw_vps_client.py # Client for OpenClaw VPS
│   └── search_service.py     # SerpAPI search skill
├── api/
│   ├── vps_routes.py          # VPS management endpoints
│   ├── search_routes.py       # Search skill endpoints
│   ├── content_routes.py      # Content request/distribution endpoints
│   └── dashboard_routes.py    # Dashboard UI routes
├── auth/
│   └── token_auth.py          # Shared auth middleware
└── templates/
    └── dashboard.html         # Simple dashboard UI
```

### Key Design Principles

1. **This Repl is the "delivery driver"** — it does NOT generate content. It requests content from AIA Engine and distributes it via OpenClaw VPS.
2. **Keep it lightweight** — No heavy ML models, no image processing. Just API orchestration and search.
3. **Resilient** — Handle AIA Engine being offline gracefully. Handle VPS being offline gracefully. Queue requests and retry.
4. **Secure** — Every secret in env vars, HMAC token auth, no plaintext credentials anywhere.

### Supported Influencer Personas

- **Starbright Monroe** (`starbright_monroe`) — Primary persona
- **Luna Vale** (`luna_vale`) — Secondary persona

### What Success Looks Like

1. Dashboard loads showing VPS status and AIA Engine connection
2. Can perform SerpAPI searches and see results
3. Can request image/caption generation from AIA Engine (via API call to remote Repl)
4. Can send agent tasks to OpenClaw VPS
5. Can check VPS status
6. All endpoints are properly authenticated
7. Clean error handling when AIA Engine or VPS is unreachable
