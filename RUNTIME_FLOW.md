# AIA Engine - Runtime Flow

*Last Updated: January 24, 2026*

## A Typical "Day in the Life"

### Morning: Content Generation Cycle

```
1. Admin opens Dashboard at /dashboard
   ↓
2. Clicks "RUN_DAILY_CYCLE" button
   ↓
3. POST /daily_cycle triggers Orchestrator
   ↓
4. For each influencer (Starbright, Luna):
   a. Load tuning profile from tuning_profiles/{influencer}.json
   b. PoseExpressionAgent selects next pose (rotates to avoid repetition)
   c. PromptBuilder constructs hyper-realistic prompt
   d. PromptSafetyFilter transforms vocabulary for content policy
   e. FalSeedreamService.generate_with_references() called:
      - Face reference: content/references/{influencer}/canonical_face/
      - Body reference: content/references/{influencer}/body_reference.png
   f. Image saved to content/generated/{influencer}/
   g. QualityAgent scores image (skin realism, face consistency, etc.)
   h. approval_status.json updated
   ↓
5. Dashboard displays new images in Gallery tab
```

### Telegram Bot Interactions (DEPRECATED - January 2026)

> **Note:** Telegram monetization discontinued. 18 users acquired, 0 paid conversions. Code preserved in `app/telegram/` but workflow stopped. Primary monetization shifted to DFans.

<details>
<summary>Archived Telegram Flow (Click to expand)</summary>

```
User sends message to @StarbrightMonroeBot
   ↓
MessageHandler receives via Telegram polling
   ↓
db.get_or_create_user() - fetch/create user record
   ↓
Check subscription tier:
   - Free: 20 messages/month
   - Companion ($9.99): 500 messages/month
   - VIP ($24.99): Unlimited
   ↓
ConversationEngine.generate_response()
   ↓
Send response via Telegram
```

</details>

### Content Approval Workflow

```
Admin views Gallery → Pending filter
   ↓
Hover over image → Action buttons appear
   ↓
[✓] Approve → GET /workflow/approve?path=...
   - Move to content/final/{influencer}/
   - Update approval_status.json
   ↓
[Loop] Create Microloop → POST /micro_loop/generate
   - MicroMovementAgent selects movement type
   - Fal.ai Kling v2.1 generates 5-second video
   - Video saved to content/loops/{influencer}/
   ↓
[Share] Twitter post flow:
   - CaptionAgent generates engaging caption
   - HashtagOptimizer adds AI-free dynamic hashtags
   - MusicOptimizationAgent suggests background audio
   - POST /api/twitter/post_full with media
```

---

## Scheduled vs Event-Driven

### Manual/Scheduled (via Admin action)

| Action | Trigger | Frequency | Status |
|--------|---------|-----------|--------|
| Daily content generation | Dashboard button / API call | Daily | Active |
| Calendar generation | Dashboard Calendar tab | Weekly/Monthly | Active |
| ~~Drip onboarding~~ | ~~POST /api/telegram/run-onboarding~~ | ~~Daily~~ | Deprecated |
| ~~Content drops~~ | ~~POST /api/telegram/send-content-drop~~ | ~~Weekly~~ | Deprecated |

### Event-Driven (automatic)

| Event | Trigger | Action | Status |
|-------|---------|--------|--------|
| Stripe payment | Stripe webhook | Payment confirmation | Active |
| ~~New Telegram message~~ | ~~User message~~ | ~~AI response~~ | Deprecated |
| ~~Subscription cancelled~~ | ~~Stripe webhook~~ | ~~Win-back message~~ | Deprecated |

---

## Posting & Messaging Flow

### Twitter/X Posting

```
Image approved in Gallery
   ↓
Admin clicks Share → Twitter dialog opens
   ↓
Live preview with toggles:
   - Music optimization (add trending audio)
   - Hashtag optimization (AI-generated, no #ai tags)
   - CTA optimization (Grok-powered)
   ↓
Admin clicks "Post to Twitter"
   ↓
1. OAuth 1.0a: Upload media to upload.twitter.com
2. Get media_id from response
3. OAuth 2.0: POST tweet with media_id
4. Tweet URL returned to admin
```

### Telegram Content Delivery (DEPRECATED)

> Telegram content delivery discontinued. See DFans integration for current monetization flow.

---

## Error Handling & Retries

### Image Generation Failures

```
FalSeedreamService.generate_with_references()
   ↓
Attempt 1: Fal.ai queue.fal.run
   ↓
If 429 (rate limit): Wait 30s, retry
If 500 (server error): Retry up to 3 times
If content policy rejection:
   ↓
   PromptSafetyFilter applies fallback vocabulary
   Retry with sanitized prompt
   ↓
If still fails: Log error, skip to next generation
```

### Stripe Webhook Failures

```
POST /api/stripe/webhook
   ↓
Verify signature with STRIPE_WEBHOOK_SECRET
   ↓
If signature invalid: Return 400, logged as security event
   ↓
If processing fails:
   - Return 500 (Stripe will retry)
   - Stripe retries for up to 3 days
```

### Telegram API Errors (DEPRECATED)

> Telegram integration discontinued. Error handling preserved in `app/telegram/` if needed for future integrations.

### AI Conversation Errors (DEPRECATED)

> Telegram conversation engine discontinued. Error handling preserved in `app/telegram/conversation_engine.py` if needed for future chat integrations.

---

## Monitoring & Observability

### Logging

- **FastAPI**: Standard Python logging to stdout
- **Workflows**: Logs visible in Replit dashboard

### Key Metrics Available

| Endpoint | Metric | Status |
|----------|--------|--------|
| `/health` | Server status, uptime | Active |
| `/api/curation/stats` | Pending/approved/rejected counts | Active |
| `/workflow/stats` | Pipeline statistics | Active |
| `/admin/stats` | Comprehensive system stats | Active |
| ~~`/api/telegram/stats`~~ | ~~User counts, subscriptions~~ | Deprecated |

### State Files to Monitor

| File | Purpose | Status |
|------|---------|--------|
| `approval_status.json` | Image workflow status | Active |
| `content/pose_history.json` | Pose rotation tracking | Active |
| ~~`telegram_users.db`~~ | ~~Telegram user/subscription data~~ | Deprecated |
