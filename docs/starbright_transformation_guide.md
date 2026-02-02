# Starbright Monroe - Image Transformation System

## Overview
AI-powered influencer content generation using Fal.ai Seedream 4.5 to transform source images into Starbright Monroe's likeness while preserving poses and outfits.

## Starbright Monroe Identity Specification

### Face
- Delicate symmetrical face
- Large round hazel-green eyes
- Natural arched eyebrows
- Small nose
- Full natural lips
- Light freckles across cheeks
- High cheekbones

### Body
- Slim healthy petite body (NOT skeletal/underweight)
- Natural proportions
- Small A-cup chest
- Reference: `content/references/starbright_monroe/body_reference.webp`

### Hair
- Color: MUST be honey-brown (NOT black, NOT dark)
- Style: Can match source image (straight, wavy, ponytail, etc.)
- Length: Long

### Reference Images
- Face: `content/references/starbright_monroe/starbright_face_reference_v3.webp`
- Body (front): `content/references/starbright_monroe/body_reference.webp`
- Body (back): `content/references/starbright_monroe/body_reference_back.webp` (if available)

---

## Issues & Solutions Tracker

### Issue 1: Combined Bedroom/Living Room Backgrounds
**Status:** IN PROGRESS

**Problem:**
Generated backgrounds show open-plan luxury penthouses with both bedroom (bed) and living room (sofa) visible in the same frame. Intimate content like lingerie should be in a dedicated bedroom, not standing in the middle of a combined loft space.

**Examples:**
- Red lingerie image placed in middle of loft with bed AND living area visible
- Should be: Pure bedroom with bed as focal point, no living area visible

**Solution:**
1. Generate dedicated background images for each scenario:
   - Pure bedroom (no living room elements)
   - Pure living room (no bedroom elements)
   - Bathroom
   - Gym
   - Studio (white/dark)
2. Update background descriptions to explicitly exclude cross-room elements
3. Use Grok vision to analyze source and map to SEPARATE room types

**Background Presets (Updated):**
```
apartment_bedroom_day: "Luxury bedroom interior only, king bed with rumpled white sheets, nightstands, soft morning light through sheer curtains, NO living room, NO sofa, NO dining area visible"

apartment_bedroom_night: "Luxury bedroom interior only, king bed, warm ambient lighting, city lights through window, NO living room, NO sofa visible"

apartment_living_day: "Luxury living room only, designer sofa, coffee table, floor-to-ceiling windows, bright daylight, NO bed, NO bedroom visible"

apartment_living_night: "Luxury living room only, designer sofa, warm evening lighting, city skyline view, NO bed, NO bedroom visible"
```

---

### Issue 2: Body Type Influence from Source
**Status:** IN PROGRESS

**Problem:**
The source model's very thin/skeletal body proportions are bleeding through despite providing a body reference image. Starbright should have a slim HEALTHY petite body, not an underweight appearance.

**Root Cause:**
The prompt wasn't explicit enough about prioritizing the body reference over the source image's body.

**Solution:**
Use stronger, more explicit prompt language:

**Old approach:**
```
"Transform person in Figure 1 to match Figure 2 (face) and Figure 3 (body)"
```

**New approach:**
```
"Generate image with:
- Face: EXACTLY from Figure 2 (hazel-green eyes, freckles, delicate features)
- Body: EXACTLY from Figure 3 (slim healthy petite, A-cup, natural proportions)
- From Figure 1 ONLY copy: pose position, outfit/clothing, hairstyle

CRITICAL: Do NOT use body proportions from Figure 1. The body MUST match Figure 3's healthy natural proportions, not the thin/skeletal build in Figure 1."
```

**Additional measures:**
- Add concrete body descriptors as anchors in every prompt
- Use negative prompt: "skeletal, underweight, anorexic, too thin, emaciated"
- Consider reference_strength parameter if available

---

### Issue 3: Hair Color Consistency
**Status:** RESOLVED

**Problem:**
Source models often have black/dark hair which was bleeding through.

**Solution:**
- Explicit prompt: "Hair color MUST be honey-brown"
- Negative prompt: "black hair, dark hair"
- Allow hairstyle to match source (straight, wavy, ponytail, etc.)

---

## Technical Implementation

### Pipeline Architecture
1. **Source Analysis (Grok Vision)**
   - Analyze source image background with `grok-2-vision-1212`
   - Extract: room type, lighting, time of day
   - Map to our preset backgrounds

2. **Background Matching**
   - Map Grok analysis to preset background descriptions
   - Ensure PURE room types (no combined spaces)

3. **Transformation (Seedream 4.5)**
   - Endpoint: `fal-ai/bytedance/seedream/v4.5/edit`
   - Up to 10 reference images supported
   - Use explicit Figure numbering for face/body/source references

### Key Files
- `app/services/background_analyzer.py` - Grok vision background analysis
- `app/services/fal_seedream_service.py` - Primary Seedream 4.5 service
- `transform_with_analysis.py` - Main transformation script
- `data/tuning_profiles/starbright_monroe_tuning.json` - Character tuning

### Seedream 4.5 Best Practices (from fal.ai docs)
- **Reference strength**: 0.5-0.7 for editing
- **Denoise strength**: 0.25-0.40 (lower = less face drift)
- **CFG scale**: 4.5-6.0
- **Concrete descriptors**: Repeat identity anchors in every prompt
- **Multi-reference**: Can specify face, body, background from different images

---

## Background Reference Images

We have dedicated background reference images for consistency:

### Bedroom
- **File**: `content/references/backgrounds/modern_luxury_bedroom.png`
- **Style**: Clean modern luxury, white/cream tufted headboard platform bed with LED under-lighting, sheer curtains, floor-to-ceiling windows, minimalist abstract art, warm neutral tones

### Living Room  
- **File**: `content/references/backgrounds/modern_luxury_living_room.png`
- **Style**: Modern luxury penthouse, white sofas (hero images show black leather sofa variant), floor-to-ceiling windows with city view, modern fireplace, crystal chandelier

### Design Guidelines
- Bedroom: White bed, clean modern minimalist
- Living room: Black leather furniture for consistency with hero images
- All rooms: Floor-to-ceiling windows, hardwood floors, modern luxury finishes

---

## Testing Results

### Test Batch: 2025-02-02 (v3)

| Image | Source Background | Matched Preset | Body Result | Background Result |
|-------|------------------|----------------|-------------|-------------------|
| Superman shirt | White studio | studio_white | TOO THIN - needs fix | Good (studio) |
| Red lingerie | Bedroom vanity | apartment_bedroom_day | OK | BAD - combined loft |
| White bra + red shorts | Plain room | apartment_bedroom_day | OK | BAD - combined loft |

### Test Batch: 2025-02-02 (v4 - stronger body reference)

| Image | Outfit Detected | Background Match | Result |
|-------|-----------------|------------------|--------|
| White bra + red shorts | White bra and red shorts | apartment_bedroom_day (override) | GOOD - pure bedroom, healthy body |
| Superman shirt | Black t-shirt, denim shorts | studio_white | FAILED - generated 2 people |

**Issue Found**: Using "Figure 1/2/3" prompt language confused the model into generating multiple people instead of one transformed person.

### Test Batch: 2025-02-02 (v5 - restructured prompt)

| Image | Outfit | Preset | Result |
|-------|--------|--------|--------|
| White bra + red shorts | White bra and red shorts | apartment_bedroom_day (override) | ✓ Pure bedroom, healthy body, honey-brown pigtails |
| Superman shirt | Black t-shirt, denim shorts, heels | apartment_living_day | ✓ ONE person (fixed!), living room, good proportions |
| Red lingerie | Red lace lingerie | apartment_bedroom_day (override) | ✓ Pure bedroom with vanity, pose preserved |

**V5 Fixes Applied:**
- Removed "Figure 1/2/3" language that confused model into generating multiple people
- Changed to clear natural language prompt structure
- Added "multiple people, two people" to negative prompt
- Outfit-based background override working correctly (lingerie → bedroom)
- Auto-copy to gallery implemented

**Remaining to refine:**
- Living room shows cream sofas - should be black leather for consistency

---

## Next Steps
1. [x] Update background descriptions to enforce PURE room types
2. [x] Test stronger body reference prompt language
3. [x] Found existing background reference images
4. [x] Fix prompt structure to avoid multiple-person generation
5. [x] Always copy generated images to gallery
6. [ ] Update living room description to use black leather furniture
7. [ ] Full batch re-run with final configuration
8. [ ] Document final working configuration

---

## Version History
- v1: Initial transformation with basic prompts
- v2: Added face reference conditioning
- v3: Added Grok background analysis, body reference, hair color enforcement
- v4: (In progress) Stronger body reference, pure room backgrounds
