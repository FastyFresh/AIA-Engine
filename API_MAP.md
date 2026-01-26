# AIA Engine - API Map

## Internal Endpoints (FastAPI Routes)

### Core Routes
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/` | Redirect to dashboard | None |
| GET | `/dashboard` | React SPA dashboard | None |
| GET | `/health` | Health check | None |
| GET | `/landing` | Public landing page | None |

### Content Generation
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/daily_cycle` | View daily cycle status | None |
| POST | `/daily_cycle` | Run full content generation cycle | None |
| GET | `/generate` | Generate single image | None |
| POST | `/pipeline/run` | Execute content pipeline | None |
| GET | `/pipeline/status` | Pipeline status | None |

### Gallery Management
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/gallery` | Gallery metadata | None |
| GET | `/gallery/images/{influencer}` | List influencer images | None |
| GET | `/gallery/image/{path}` | Serve single image | None |
| GET | `/gallery/download/{path}` | Download single image | None |
| GET | `/gallery/download-all/{influencer}` | ZIP download all | None |
| GET | `/workflow/approve` | Approve image | None |
| GET | `/workflow/reject` | Reject image | None |
| DELETE | `/content/delete` | Delete content | None |

### Micro-Loop Video
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/micro_loop/hero_refs` | List hero references | None |
| POST | `/micro_loop/upload_hero` | Upload hero image | None |
| POST | `/micro_loop/generate` | Generate microloop video | None |
| GET | `/micro_loop/list` | List generated videos | None |
| GET | `/micro_loop/video/{path}` | Serve video file | None |
| POST | `/micro_loop/caption` | Generate video caption | None |

### Face/Identity Transfer
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/face_swap` | Face swap status | None |
| POST | `/face_swap` | Execute face swap | None |
| POST | `/api/identity/transfer` | Identity transfer | None |
| POST | `/api/pose/transfer` | Pose transfer | None |

### Image Generation (Seedream4)
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/seedream4/generate` | Generate with Seedream4 | None |
| GET | `/api/seedream4/presets` | Generation presets | None |
| POST | `/api/seedream4/face-swap` | Face swap on generated | None |

### Unified Content Agent
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/unified/influencers` | List influencers | None |
| POST | `/api/unified/generate` | Generate unified content | None |
| POST | `/api/unified/generate-weekly` | Weekly batch generation | None |

### Curation
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/curation/stats` | Curation statistics | None |
| GET | `/api/curation/pending` | Pending review items | None |
| POST | `/api/curation/score` | Score single image | None |
| POST | `/api/curation/approve` | Approve image | None |
| POST | `/api/curation/reject` | Reject image | None |

### LoRA Training
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/lora/upload` | Upload LoRA model | None |
| POST | `/api/lora/generate` | Generate with LoRA | None |
| GET | `/api/lora/status` | Training status | None |

### Twitter Integration
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/twitter/status` | Connection status | None |
| GET | `/api/twitter/auth` | OAuth2 flow start | None |
| GET | `/api/twitter/callback` | OAuth2 callback | None |
| POST | `/api/twitter/post` | Post to Twitter | OAuth tokens |

### Calendar & Scheduling
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/calendar/generate/week` | Generate week plan | None |
| GET | `/api/calendar/generate/month` | Generate month plan | None |
| GET | `/api/calendar/today` | Today's schedule | None |

### Research
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/research/analyze` | Analyze competitor | None |
| GET | `/api/research/scrape/{username}` | Scrape Instagram | None |
| POST | `/api/research/generate-prompts` | Generate from research | None |

### Music
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/music/tracks` | List music tracks | None |
| POST | `/api/music/upload` | Upload track | None |
| POST | `/api/music/merge` | Merge audio to video | None |

### CTA Optimization
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/cta/optimize` | Optimize CTA | None |
| GET | `/api/cta/bio` | Generate bio | None |
| GET | `/api/cta/post` | Generate post CTA | None |

### Stripe Payments
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/stripe/webhook` | Stripe webhook handler | Stripe signature |
| GET | `/payment/success` | Payment success page | None |
| GET | `/payment/cancel` | Payment cancel page | None |

### Telegram Admin (Protected)
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/telegram/stats` | Bot statistics | None |
| POST | `/api/telegram/run-onboarding` | Run drip campaigns | ADMIN_API_KEY |
| POST | `/api/telegram/send-content-drop` | Send to subscribers | ADMIN_API_KEY |
| POST | `/api/telegram/send-teaser` | Send to free users | ADMIN_API_KEY |
| POST | `/api/telegram/upload-content` | Upload bot content | None |

### Admin Dashboard
| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/admin` | Admin dashboard page | None |
| POST | `/admin/verify` | Verify admin access | ADMIN_API_KEY |
| GET | `/admin/stats` | System statistics | ADMIN_API_KEY |

---

## Outbound API Calls

### Fal.ai
| URL Pattern | Purpose | Auth |
|-------------|---------|------|
| `https://queue.fal.run/fal-ai/seedream-4.5-edit` | Image generation | FAL_KEY header |
| `https://queue.fal.run/fal-ai/kling-video/v2.1/image-to-video` | Video generation | FAL_KEY header |
| `https://queue.fal.run/fal-ai/flux-lora` | LoRA generation | FAL_KEY header |
| `https://queue.fal.run/fal-ai/face-swap` | Face swap | FAL_KEY header |

### Replicate
| URL Pattern | Purpose | Auth |
|-------------|---------|------|
| `https://api.replicate.com/v1/predictions` | Image/video generation | Bearer REPLICATE_API_TOKEN |

### OpenRouter / XAI
| URL Pattern | Purpose | Auth |
|-------------|---------|------|
| `https://openrouter.ai/api/v1/chat/completions` | AI conversation | Bearer OPENROUTER_API_KEY |
| `https://api.x.ai/v1/chat/completions` | Grok AI (captions, hashtags) | Bearer XAI_API_KEY |

### Stripe
| URL Pattern | Purpose | Auth |
|-------------|---------|------|
| `https://api.stripe.com/v1/checkout/sessions` | Create checkout | STRIPE_SECRET_KEY |
| `https://api.stripe.com/v1/customers` | Manage customers | STRIPE_SECRET_KEY |

### Twitter
| URL Pattern | Purpose | Auth |
|-------------|---------|------|
| `https://api.twitter.com/2/tweets` | Post tweets | OAuth 2.0 |
| `https://upload.twitter.com/1.1/media/upload.json` | Upload media | OAuth 1.0a |

### Telegram
| URL Pattern | Purpose | Auth |
|-------------|---------|------|
| `https://api.telegram.org/bot{token}/*` | Bot API | Bot token in URL |

### Apify
| URL Pattern | Purpose | Auth |
|-------------|---------|------|
| `https://api.apify.com/v2/acts/*/runs` | Instagram scraping | Bearer APIFY_API_TOKEN |

---

## Webhooks Received

| Endpoint | Source | Events | Auth |
|----------|--------|--------|------|
| `POST /api/stripe/webhook` | Stripe | checkout.session.completed, customer.subscription.deleted | Stripe-Signature (HMAC) |

---

## Authentication Methods Summary

| Method | Used By | Location |
|--------|---------|----------|
| **API Key Header** | Admin endpoints | `X-Admin-Key: {ADMIN_API_KEY}` |
| **Bearer Token** | Replicate, OpenRouter, XAI, Apify | `Authorization: Bearer {token}` |
| **Custom Header** | Fal.ai | `Authorization: Key {FAL_KEY}` |
| **OAuth 1.0a** | Twitter media upload | HMAC-SHA1 signature |
| **OAuth 2.0** | Twitter posting | Bearer access token |
| **Webhook Signature** | Stripe | `Stripe-Signature` header (HMAC-SHA256) |
| **URL Token** | Telegram | Bot token in URL path |
