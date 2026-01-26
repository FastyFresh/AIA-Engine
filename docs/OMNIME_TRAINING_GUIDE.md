# OmniMe AI Training Guide

## Overview
OmniMe is an AI platform that creates hyper-realistic virtual influencer "twins" from photos. Upload 8-20 clear portraits, define your style, and the AI generates photos and videos without physical shoots.

---

## Optimal Training Image Requirements

### Quantity
- **Maximum**: 12 photos (platform limit)
- **Recommended**: 12 diverse, high-quality images
- **Strategy**: Maximize variety within the 12-image limit

### Technical Specifications
| Requirement | Specification |
|-------------|---------------|
| Resolution | Minimum 1080p, prefer 4K |
| Format | JPEG, PNG (no compression artifacts) |
| Orientation | Portrait preferred |
| Face visibility | Unobstructed, no sunglasses/hats |
| Background | Clean, minimal distractions |

---

## Optimal 12-Image Distribution

For the maximum 12 images, prioritize this mix:

| Category | Count | Priority |
|----------|-------|----------|
| Expressions | 5 | Highest - captures personality |
| Angles | 3 | High - trains facial structure |
| Body Poses | 3 | Medium - for full-body content |
| Gestures | 1 | Lower - enhances dynamics |

---

## Required Image Categories

### 1. FACIAL EXPRESSIONS (5 images recommended)
These train the AI to recreate natural expressions:

| # | Expression | Description |
|---|------------|-------------|
| 1 | Neutral | Relaxed, resting face |
| 2 | Soft smile | Lips closed, gentle smile |
| 3 | Full smile | Teeth showing, genuine |
| 4 | Serious/focused | Concentrated look |
| 5 | Raised eyebrows | Surprised/interested |
| 6 | Slight smirk | Confident, playful |
| 7 | Thoughtful | Looking slightly up/away then back |
| 8 | Laugh | Mid-laugh, natural joy |

### 2. ANGLES (3 images recommended)
Train facial structure from multiple perspectives:

| # | Angle | Description |
|---|-------|-------------|
| 1 | Front-facing | Direct eye contact (PRIMARY) |
| 2 | Slight left turn | 15-20° rotation |
| 3 | Slight right turn | 15-20° rotation |
| 4 | Slight head tilt left | Chin up slightly |
| 5 | Slight head tilt right | Casual, relaxed |
| 6 | Looking up at camera | Selfie angle, flattering |

### 3. BODY POSES (3 images recommended)
For full-body content generation:

| # | Pose | Description |
|---|------|-------------|
| 1 | Standing natural | Relaxed shoulders, weight even |
| 2 | Arms crossed | Professional, confident |
| 3 | Hands on hips | Assertive, engaged |
| 4 | One hand raised | Interactive gesture |
| 5 | Leaning forward | Engaged, active |
| 6 | Seated casual | Relaxed, approachable |

### 4. GESTURES (1 image recommended)
For dynamic video content:

| # | Gesture | Description |
|---|---------|-------------|
| 1 | Open hands | Conversational, welcoming |
| 2 | Pointing | For interactive content |
| 3 | Expressive hands | Emphasizing points |
| 4 | Hair touch | Natural, candid moment |

---

## Lighting Requirements

### Best Options (in order)
1. **Golden hour** - Sunrise/sunset soft warm light
2. **Window light** - Natural, diffused indoor light
3. **Ring light** - 5500K daylight temperature
4. **Softbox setup** - Professional even lighting

### Avoid
- Harsh direct sunlight
- Mixed lighting (indoor + outdoor)
- Strong shadows on face
- Overexposed/blown out areas
- Flash photography

---

## Prompt List for Dataset Creation

Use these prompts with your existing image generation system to create OmniMe training images.

---

### PRIORITY 12: Optimized for OmniMe's Limit

These 12 prompts are prioritized for maximum training quality:

```
1. "Front-facing portrait, neutral relaxed expression, direct eye contact, soft natural lighting, clean background"

2. "Front-facing portrait, soft gentle smile lips closed, warm inviting expression, direct eye contact"

3. "Front-facing portrait, full genuine smile showing teeth, happy joyful expression, natural lighting"

4. "Front-facing portrait, serious focused expression, intense direct gaze, professional look"

5. "Front-facing portrait, confident slight smirk, playful knowing expression, natural lighting"

6. "Portrait with face turned 15 degrees left, soft smile, three-quarter view, natural lighting"

7. "Portrait with face turned 15 degrees right, neutral expression, three-quarter view"

8. "Portrait with slight head tilt, direct eye contact, relaxed casual expression"

9. "Full body standing naturally, relaxed shoulders, confident stance, neutral expression, clean background"

10. "Full body standing with arms crossed, professional confident posture, slight smile"

11. "Full body standing hands on hips, assertive engaged pose, confident expression"

12. "Upper body portrait with open welcoming hand gesture, conversational pose, friendly expression"
```

---

### FULL PROMPT LIBRARY (24 options)

Choose from these if you want alternatives:

### EXPRESSIONS SET
```
1. "Front-facing portrait, neutral relaxed expression, direct eye contact, soft natural lighting, clean background, high resolution"

2. "Front-facing portrait, soft gentle smile lips closed, warm inviting expression, direct eye contact, natural lighting"

3. "Front-facing portrait, full genuine smile showing teeth, happy joyful expression, eye crinkles, natural lighting"

4. "Front-facing portrait, serious focused expression, intense direct gaze, professional look, even lighting"

5. "Front-facing portrait, raised eyebrows interested expression, slight surprise, engaged look, soft lighting"

6. "Front-facing portrait, confident slight smirk, knowing expression, self-assured, natural lighting"

7. "Front-facing portrait, thoughtful expression, looking slightly upward, contemplative, soft lighting"

8. "Front-facing portrait, mid-laugh genuine joy, natural candid moment, happy expression, warm lighting"
```

### ANGLES SET
```
9. "Portrait with face turned 15 degrees left, soft smile, three-quarter view, natural lighting"

10. "Portrait with face turned 15 degrees right, neutral expression, three-quarter view, even lighting"

11. "Portrait with head tilted slightly left, chin up, confident expression, soft lighting"

12. "Portrait with head tilted slightly right, relaxed casual expression, natural lighting"

13. "Portrait from slightly below eye level, looking down at camera, flattering selfie angle, warm lighting"

14. "Portrait with slight chin tuck, direct eye contact, approachable expression, soft lighting"
```

### BODY POSES SET
```
15. "Full body standing naturally, relaxed shoulders, weight evenly distributed, confident stance, neutral expression, clean background"

16. "Full body standing with arms crossed, professional confident posture, slight smile, business casual"

17. "Full body standing hands on hips, assertive engaged pose, confident expression, natural lighting"

18. "Full body standing one hand slightly raised, interactive gesture, approachable expression, clean background"

19. "Full body leaning slightly forward, engaged active posture, interested expression, natural setting"

20. "Seated casual pose, relaxed approachable body language, soft smile, natural lighting"
```

### GESTURES SET
```
21. "Upper body portrait with open welcoming hand gesture, conversational pose, friendly expression, natural lighting"

22. "Upper body portrait with pointing gesture, interactive engaged expression, professional setting"

23. "Upper body portrait with expressive hand gestures near face, animated speaking pose, natural expression"

24. "Upper body portrait touching hair casually, candid natural moment, relaxed expression, soft lighting"
```

---

## Quick Reference Checklist

### Before Shooting/Generating
- [ ] Clean, minimal background prepared
- [ ] Lighting set up (natural or ring light)
- [ ] Camera/settings at high resolution
- [ ] Expression list ready

### Image Set Composition (12 max)
- [ ] 5 different expressions (neutral, soft smile, full smile, serious, smirk)
- [ ] 3 different angles (front + slight left/right turns)
- [ ] 3 body poses (standing natural, arms crossed, hands on hips)
- [ ] 1 gesture variation (open hands/conversational)
- [ ] All with direct eye contact as primary focus

### Quality Check
- [ ] No harsh shadows on face
- [ ] Face clearly visible in all shots
- [ ] No motion blur
- [ ] Consistent person across all images
- [ ] High resolution (1080p minimum)

---

## Integration with AIA Engine

To generate OmniMe training images using the existing pipeline:

```python
from app.services.fal_seedream_service import FalSeedreamService

service = FalSeedreamService(influencer_id="starbright_monroe")

# Generate expression set
prompts = [
    "front-facing portrait, neutral relaxed expression, direct eye contact",
    "front-facing portrait, soft gentle smile, warm expression",
    # ... add all prompts from list above
]

for i, prompt in enumerate(prompts):
    result = await service.generate_with_references(
        prompt=prompt,
        aspect_ratio="portrait_4_3",
        filename_prefix=f"omnime_training_{i+1:02d}"
    )
```

---

## Expected Results
- Training time: Minutes (not hours)
- Daily output: 10-30 content pieces (plan-dependent)
- Output types: Photos and 10-second videos
- Platforms: Instagram, TikTok, YouTube Shorts, LinkedIn

---

*Last updated: December 14, 2024*
