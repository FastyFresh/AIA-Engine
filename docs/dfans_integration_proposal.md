# DFans API Integration Proposal

## Overview

We operate AI-powered companion bots for two influencer personas (Starbright Monroe and Luna Vale) on Telegram. We're seeking to extend this capability to DFans, where fans can have personalized AI conversations while payments and content hosting remain entirely on the DFans platform.

---

## Current Telegram Bot Architecture

### How It Works

1. **Fan sends message** → Telegram delivers to our bot
2. **AI generates response** → Using persona-specific prompts and conversation history
3. **Bot sends reply** → Delivered back through Telegram
4. **Optional: Send photo/content** → Based on subscription tier

### Technical Stack

| Component | Technology |
|-----------|------------|
| AI Provider | OpenRouter (primary), Grok/xAI (fallback) |
| Conversation Memory | SQLite with full history per user |
| Payments | Stripe (subscriptions + tips) |
| Content Delivery | Photo/video via Telegram API |
| Hosting | Replit (Python/FastAPI backend) |

---

## Persona Details

### Starbright Monroe (@starbrightnight)
- **Personality**: Warm, flirty, playful, direct
- **Voice**: Casual texting style, uses "heyy", emojis sparingly
- **Age**: 19, college student / barista
- **Audience**: Men 20-60

### Luna Vale
- **Personality**: Gentle, thoughtful, emotionally present, quietly confident
- **Voice**: Soft, intimate, artistic
- **Audience**: Men 20-40

---

## Subscription Tiers

| Tier | Price | Messages | Features |
|------|-------|----------|----------|
| Free | $0 | 20/month | Basic conversation, weekly teasers |
| Companion | $9.99/mo | 500/month | Priority responses, exclusive photos, voice messages |
| VIP | $24.99/mo | Unlimited | Custom requests, video content, personal relationship |

---

## Proposed DFans Integration Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   DFans     │────▶│  Our Server  │────▶│   DFans     │
│  (Webhook)  │     │  (AI Engine) │     │   (API)     │
└─────────────┘     └──────────────┘     └─────────────┘
     │                     │                    │
     │ Fan sends           │ Generate           │ Send reply
     │ message             │ AI response        │ (+ unlock?)
     └─────────────────────┴────────────────────┘
```

### What We Need from DFans

1. **Incoming Webhook** - Notify us when a fan sends a message
   - Fan user ID (for conversation history)
   - Message content
   - Subscription tier (for response differentiation)

2. **Send Reply API** - Endpoint to send AI-generated response back
   - Text message
   - Optional: Media attachment

3. **Authentication** - API key or OAuth token for our server

4. **Optional: Content Unlock API** - Trigger specific content unlock
   - Our AI might say "here's something special for you" and unlock a photo

### What Stays on DFans

- All payment processing
- All content hosting
- Subscription management
- Fan identity/accounts

### What We Handle

- AI conversation generation
- Persona personality consistency
- Conversation memory/context
- Response timing and pacing

---

## Revenue Model

Currently on Telegram:
- Subscriptions: $9.99 - $24.99/month per tier
- Tips: $5 - $100+ one-time
- Early stage: Building subscriber base, revenue growing

Happy to discuss revenue share models that work for both parties.

---

## Sample Conversation

**Fan**: hey starbright, how's your day going?

**AI Response**: 
```
heyy you 💕

omg my day just got better now that you're here

was just making coffee... you know how I am with my caffeine lol

what about you? what are you up to?
```

**Fan**: just thinking about you tbh

**AI Response**:
```
wait really? 😊

that's so sweet... I like that you think about me

what were you thinking about specifically? 

don't be shy 😏
```

---

## Technical Requirements

### Our API Endpoint (Webhook Receiver)
```
POST /api/dfans/webhook
Content-Type: application/json
Authorization: Bearer <DFANS_API_KEY>

{
  "event": "message.received",
  "fan_id": "12345",
  "creator_id": "starbrightnight",
  "message": "hey, how are you?",
  "tier": "vip",
  "timestamp": "2024-12-30T12:00:00Z"
}
```

### Our Response
```json
{
  "status": "ok",
  "response_text": "heyy you 💕 I'm good! just thinking about...",
  "unlock_content_id": null
}
```

---

## Next Steps

1. DFans provides API documentation / webhook specs
2. We build and test integration endpoint
3. Pilot with Starbright account
4. Monitor and iterate

---

## Contact

Ready to discuss technical details or hop on a call to walk through the architecture.
