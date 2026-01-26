# Telegram Bot Monetization System - Technical Documentation

## Overview

This document provides comprehensive technical documentation for the AI Influencer Telegram Bot system. The platform enables AI-powered conversational experiences with tiered subscription monetization, automated content delivery, and Stripe payment integration.

**Business Model**: AI influencer personas (Starbright Monroe, Luna Vale) engage users in personalized conversations, with monetization through tiered subscriptions offering exclusive content access.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Telegram Users ◄──► Telegram API ◄──► Bot Handler (python-telegram-bot)
│                                                                      │
│  Admin Dashboard (React) ◄──► FastAPI Backend                       │
│                                                                      │
│  Stripe Checkout ◄──► Stripe Webhooks                               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│  FastAPI Backend (app/main.py)                                       │
│  ├── Stripe Webhook Handler (/api/stripe/webhook)                   │
│  ├── Admin Content APIs (/api/telegram/*)                           │
│  └── AI Services (XAI/Grok, Fal.ai)                                 │
│                                                                      │
│  Telegram Bot Worker (app/telegram/run_bots.py)                     │
│  ├── InfluencerBot instances (per persona)                          │
│  ├── ConversationEngine (AI-powered chat)                           │
│  └── ContentService (media delivery)                                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
├─────────────────────────────────────────────────────────────────────┤
│  SQLite Database (data/telegram_users.db)                           │
│  ├── users (profiles, subscriptions, message counts)                │
│  ├── chat_history (conversation context)                            │
│  ├── onboarding_status (drip campaign tracking)                     │
│  └── content_drops (delivery logs)                                  │
│                                                                      │
│  Content Storage (content/telegram/{persona}/{tier}/)               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Bot Handler (`app/telegram/bot_handler.py`)

The `InfluencerBot` class manages all Telegram interactions for a single persona. The bot logic is split into focused modules for maintainability (refactored December 2024).

**Module Structure:**
| Module | Class | Purpose |
|--------|-------|---------|
| `bot_handler.py` | `InfluencerBot` | Core orchestration, command routing |
| `payments.py` | `PaymentHandler` | Stripe checkout, subscription/tip flows |
| `content.py` | `ContentManager` | Photo detection, content delivery |
| `conversation_engine.py` | `ConversationEngine` | AI-powered persona conversations |
| `user_database.py` | `TelegramDatabase` | SQLite with versioned migrations |
| `bot_config.py` | - | Persona configs, Stripe price mappings |

**Key Responsibilities:**
- Message handling and routing (delegates to PaymentHandler/ContentManager)
- Subscription tier enforcement
- Usage tracking and upsell triggers
- Payment flow initiation via PaymentHandler

**Command Handlers:**
| Command | Description |
|---------|-------------|
| `/start` | Welcome message, user registration |
| `/subscribe` | Display subscription options |
| `/status` | Show current tier and usage |
| `/help` | Available commands |

**Message Flow:**
```
User Message
    │
    ▼
┌──────────────────┐
│ Rate Limit Check │ ──► Block if exceeded
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Photo Request?   │ ──► Route to photo generation
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Increment Usage  │ ──► Check upsell triggers (70%, 90%)
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ ConversationEngine│ ──► AI response generation
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Send Response    │
└──────────────────┘
```

**Upsell Trigger Points:**
- 70% usage: Soft nudge with upgrade button
- 90% usage: Urgent nudge with upgrade button
- 100% usage: Block messages, show upgrade prompt

---

### 2. Conversation Engine (`app/telegram/conversation_engine.py`)

**Location**: Standalone module `app/telegram/conversation_engine.py`

Generates persona-appropriate AI responses using XAI/Grok API via OpenRouter.

**Configuration per Persona:**

| Persona | Style | Emoji Usage | Message Length |
|---------|-------|-------------|----------------|
| Starbright Monroe | Warm, intimate, curious | Minimal | 1-2 sentences |
| Luna Vale | Bold, mysterious, direct | Rare | Short, punchy |

**Context Management:**
- Maintains rolling chat history (last 10-20 messages)
- Includes user preferences and subscription tier in context
- Photo request detection via keyword matching

---

### 3. Content Manager (`app/telegram/content.py`)

Handles all automated content delivery mechanisms. Refactored from `content_service.py` in December 2024.

**Features:**

#### Welcome Packs
Triggered automatically when subscription is upgraded via Stripe webhook.

| Tier | Content Count | Folder |
|------|---------------|--------|
| Companion | 3 images | `content/telegram/{persona}/companion/` |
| VIP | 5 images | `content/telegram/{persona}/vip/` |

**Implementation:**
```python
async def send_welcome_pack(telegram_id, tier, first_name):
    # 1. Load tier-specific config
    # 2. Get most recent images from folder
    # 3. Send personalized welcome message
    # 4. Send images with [1/N] captions
```

#### Drip Onboarding
Scheduled messages to free users encouraging conversion.

| Day | Purpose |
|-----|---------|
| 0 | Welcome, introduce exclusive content |
| 3 | Tease recent subscriber-only content |
| 7 | Final nudge, emphasize value |

#### Content Drops
Admin-triggered broadcast to subscribers of a specific tier.

```python
POST /api/telegram/send-content-drop
{
    "persona_id": "starbright_monroe",
    "content_path": "content/telegram/starbright/companion/photo.jpg",
    "caption": "Something special just for you...",
    "tier": "companion"
}
```

#### Teaser System
Watermarked preview content for free users to drive conversions.

#### Churn Win-back
Automatic message when subscription is cancelled (triggered by Stripe webhook).

---

### 4. User Database (`app/telegram/user_database.py`)

**Database**: SQLite via `aiosqlite`
**Location**: `data/telegram_users.db`

**Migration System** (Added December 2024):
- Version-tracked migrations via `schema_versions` table
- Current schema version: v2
- Prevents corruption during schema updates
- Supports safe rollbacks

**Schema:**

```sql
-- Core user table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER NOT NULL,
    persona_id TEXT NOT NULL,
    first_name TEXT,
    username TEXT,
    subscription_tier TEXT DEFAULT 'free',
    messages_used INTEGER DEFAULT 0,
    messages_limit INTEGER DEFAULT 20,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP,
    stripe_customer_id TEXT,
    preferences TEXT,  -- JSON blob
    UNIQUE(telegram_id, persona_id)
);

-- Chat history for context
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER NOT NULL,
    persona_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Onboarding tracking
CREATE TABLE onboarding_status (
    telegram_id INTEGER NOT NULL,
    persona_id TEXT NOT NULL,
    day_0_sent BOOLEAN DEFAULT FALSE,
    day_3_sent BOOLEAN DEFAULT FALSE,
    day_7_sent BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (telegram_id, persona_id)
);

-- Content delivery logs
CREATE TABLE content_drops (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER NOT NULL,
    persona_id TEXT NOT NULL,
    content_type TEXT,
    content_path TEXT,
    tier TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Methods:**
```python
class TelegramDatabase:
    async def get_or_create_user(telegram_id, persona_id, first_name=None)
    async def update_subscription(telegram_id, persona_id, tier)
    async def increment_message_count(telegram_id, persona_id)
    async def get_chat_history(telegram_id, persona_id, limit=20)
    async def add_chat_message(telegram_id, persona_id, role, content)
    async def get_subscribers_for_content(persona_id, tier)
    async def get_users_for_onboarding(persona_id, day)
```

---

### 5. Stripe Integration

**Webhook Endpoint**: `POST /api/stripe/webhook`

**Handled Events:**

| Event | Action |
|-------|--------|
| `checkout.session.completed` | Update user tier, send welcome pack |
| `customer.subscription.deleted` | Downgrade to free, send win-back message |

**Checkout Flow:**
```
1. User clicks upgrade button in Telegram
2. Bot generates Stripe Checkout URL with metadata:
   - telegram_user_id
   - persona_id  
   - tier_id
3. User completes payment on Stripe
4. Stripe sends webhook to /api/stripe/webhook
5. System updates database and sends welcome pack
```

**Stripe Products:**
| Tier | Price ID | Monthly Cost |
|------|----------|--------------|
| Companion | `price_1Sfz1iCKH1K1X3NKV9JeutLo` | $9.99 |
| VIP | `price_1Sfz3NCKH1K1X3NKbueVdkKJ` | $24.99 |

**Metadata Requirements:**
Checkout sessions MUST include:
```python
metadata = {
    "telegram_user_id": str(telegram_id),
    "persona_id": persona_id,
    "tier_id": tier
}
```

---

### 6. Admin API (`app/routes/content_admin.py`)

All endpoints require `X-Admin-Key` or `X-Api-Key` header matching `ADMIN_API_KEY`.

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/telegram/content/list` | List content in a directory |
| POST | `/api/telegram/content/move` | Move content between folders |
| GET | `/api/telegram/stats` | User and subscription statistics |
| POST | `/api/telegram/run-onboarding` | Trigger drip messages |
| POST | `/api/telegram/send-content-drop` | Broadcast to subscribers |
| POST | `/api/telegram/send-teaser` | Send teaser to free users |

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN_STARBRIGHT` | Yes | Bot token for @StarbrightMonroeBot |
| `TELEGRAM_BOT_TOKEN_LUNA` | Yes | Bot token for @LunaVale19Bot |
| `STRIPE_SECRET_KEY` | Yes | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret |
| `ADMIN_API_KEY` | Yes | Admin API authentication |
| `XAI_API_KEY` | Yes | Grok/XAI API for conversations |
| `OPENROUTER_API_KEY` | No | Alternative AI provider |
| `FAL_KEY` | No | Fal.ai for image generation |

### Content Directory Structure

```
content/
└── telegram/
    ├── starbright/
    │   ├── companion/      # Companion tier exclusive
    │   ├── vip/            # VIP tier exclusive
    │   ├── teaser/         # Free user teasers
    │   └── archive/        # Used content
    └── luna/
        ├── companion/
        ├── vip/
        ├── teaser/
        └── archive/
```

---

## Running the System

### Development

```bash
# Start FastAPI backend (port 5000)
uvicorn app.main:app --host 0.0.0.0 --port 5000

# Start Telegram bots (separate process)
python -m app.telegram.run_bots
```

### Production Workflows

Two workflows configured:
1. **AIA Engine**: FastAPI backend on port 5000
2. **Telegram Bots**: Bot polling instances

---

## Extension Guide

### Adding a New Persona

1. **Create bot via @BotFather** and obtain token
2. **Add environment variable**: `TELEGRAM_BOT_TOKEN_{NAME}`
3. **Update `bot_config.py`**:
   ```python
   PERSONA_BOTS = {
       "new_persona": {
           "token_env": "TELEGRAM_BOT_TOKEN_NEWNAME",
           "name": "New Persona Name"
       }
   }
   ```
4. **Add to content service configs** (ONBOARDING_MESSAGES, WELCOME_PACK_CONFIG)
5. **Create content directories**: `content/telegram/newpersona/{companion,vip,teaser}/`
6. **Update `run_bots.py`** to include new persona

### Adding a New Subscription Tier

1. **Create Stripe product and price**
2. **Update tier definitions** in bot_handler.py
3. **Add welcome pack config** in content_service.py
4. **Create content folder**: `content/telegram/{persona}/{tier}/`
5. **Update checkout button logic** to include new tier

### Database Migration to PostgreSQL

1. Replace `aiosqlite` with `asyncpg`
2. Update connection strings to use `DATABASE_URL`
3. Migrate schema using Drizzle or Alembic
4. Update all `TelegramDatabase` methods for PostgreSQL syntax

---

## Monitoring & Debugging

### Logs

- Backend logs: Workflow console output
- Bot logs: `app/telegram/run_bots.py` logging

### Key Metrics to Track

| Metric | Description |
|--------|-------------|
| Conversion Rate | Free → Paid users |
| Message Usage | Average messages per user per tier |
| Churn Rate | Subscription cancellations |
| Content Drop Engagement | Open/view rates |
| Welcome Pack Delivery | Success rate |

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Bot not responding | Token invalid or bot not running | Check env var, restart workflow |
| Webhook not firing | Incorrect endpoint or secret | Verify Stripe dashboard settings |
| Welcome pack empty | No images in tier folder | Add content to appropriate directory |
| Subscription not updating | Metadata missing in checkout | Ensure telegram_user_id in metadata |

---

## Security Considerations

1. **Bot Tokens**: Store in environment secrets, never commit
2. **Stripe Webhook**: Validate signature using `STRIPE_WEBHOOK_SECRET`
3. **Admin API**: Require `ADMIN_API_KEY` header on all admin endpoints
4. **User Data**: SQLite file should be in non-public directory
5. **Content**: Served only via bot, not publicly accessible
6. **Secret Logging**: Never log secret values or prefixes (fixed December 2024)
7. **Centralized Settings**: `app/settings.py` uses Pydantic SecretStr for sensitive configuration

---

## API Quick Reference

### Stripe Webhook Payload Structure

```json
{
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "metadata": {
        "telegram_user_id": "123456789",
        "persona_id": "starbright_monroe",
        "tier_id": "companion"
      }
    }
  }
}
```

### Content Drop Request

```json
POST /api/telegram/send-content-drop
Headers: { "X-Admin-Key": "your-admin-key" }
Body: {
  "persona_id": "starbright_monroe",
  "content_path": "content/telegram/starbright/companion/photo.jpg",
  "caption": "Just for you...",
  "tier": "companion"
}
```

### User Stats Response

```json
{
  "total_users": 150,
  "by_tier": {
    "free": 120,
    "companion": 25,
    "vip": 5
  },
  "by_persona": {
    "starbright_monroe": 100,
    "luna_vale": 50
  }
}
```

---

*Last Updated: December 22, 2024*
*Business Entity: Firepie LLC*
*Architecture Version: Modular (payments.py, content.py, bot_handler.py)*
