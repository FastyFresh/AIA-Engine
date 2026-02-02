# Starbright Monroe - Image Transformation System

## Overview
AI-powered influencer content generation using Fal.ai Seedream 4.5 to transform source images into Starbright Monroe's likeness while preserving poses and outfits.

## Starbright Monroe Identity Specification

### Face
- Delicate symmetrical face
- Large round hazel-brown eyes (NOT blue, NOT green)
- Natural arched eyebrows
- Small nose
- Full natural lips
- Light freckles across cheeks and nose
- High cheekbones

### Body
- Slim healthy petite body (NOT skeletal/underweight)
- Natural proportions
- Small A-cup chest
- Reference: `content/references/starbright_monroe/body_reference.webp`

### Hair
- Color: MUST be dark brown (rich brown, NOT black, NOT light/honey colored)
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

### Seedream 4.5 Best Practices (from fal.ai docs + z-image.ai research)

**Critical Parameters:**
- **Seed**: LOCK IT - reuse exact seed for entire set to prevent identity drift
- **CFG (guidance)**: 4.5–6.0 for portraits (higher pushes toward generic archetypes)
- **Denoise strength**: 0.25–0.40 sweet spot (0.5+ changes bone structure!)
- **Steps**: 28–36 (fewer = more variance, more = subtle drift toward priors)

**Identity Anchors (use concrete descriptors, NOT vague terms):**
- Write: "soft round jaw, high cheekbones, slightly wide-set hazel-green eyes, defined cupid's bow, light freckles"
- NOT: "beautiful model, cinematic lighting" (too vague, causes drift)

**Reference Strategy:**
- Use ONE strong anchor image, not multiple weak ones
- Generate a "master" shot first, save it
- Create variations changing ONLY ONE thing at a time (angle OR lighting OR background - not all)
- If identity drifts, re-inject master shot as secondary reference

**Background Consistency:**
- Use the SAME background reference image across generations
- Lock seed + keep lighting phrase constant
- For background changes: use low denoise 0.25-0.35, keep face area protected

**Editing Rules:**
- Low-strength, single-purpose passes
- Small literal edits (avoid hats covering forehead - occlusion triggers drift)
- If edit goes sideways, roll back to last stable image

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

### Test: V6 (dark brown hair focus)
- Updated hair color spec to "dark brown" (was "honey-brown")
- Added explicit "do NOT blend with source" for face
- Result: Hair still not dark enough, face still slightly blended

### Test: V7 (photorealistic + dark brown hair)
- Added "photorealistic photograph, NOT cartoon, NOT illustration" 
- Hair described as "DARK BROWN (like chocolate or espresso)"
- Negative prompts: cartoon, illustration, anime, stylized, light hair colors
- **Result: SUCCESS** - Dark brown hair, black leather furniture, photorealistic quality

**V7 Key Improvements:**
- Hair is properly dark brown ✓
- Black leather furniture in living room ✓
- More photorealistic, less cartoonish ✓
- Pose and outfit preserved ✓

---

## Next Steps
1. [x] Update background descriptions to enforce PURE room types
2. [x] Test stronger body reference prompt language
3. [x] Found existing background reference images
4. [x] Fix prompt structure to avoid multiple-person generation
5. [x] Always copy generated images to gallery
6. [x] Update living room description to use black leather furniture
7. [x] Fix hair color to dark brown
8. [x] Fix cartoonish face issue with photorealistic emphasis
9. [ ] Full batch re-run with final configuration
10. [ ] Document final working configuration

---

## Known Issues & Limitations

### Issue: Face Blending Instead of Replacement
**Status:** UNRESOLVED

Seedream 4.5 blends the source model's facial features with Starbright's reference instead of fully replacing them. This results in:
- Eye color inconsistency (blue, green, hazel variations instead of consistent hazel-brown)
- Facial structure that's a mix of source + Starbright
- Different-looking faces across images that should be identical

**Evidence from V8 test:**
- Image 1: Eyes appear blue
- Image 2: Eyes appear hazel/brown
- Image 3: Eyes appear green
- All should be consistent hazel-brown

### Issue: Pose Not Preserved
**Status:** UNRESOLVED

The model changes poses rather than preserving them exactly from the source:
- Red lingerie image: Source was standing at vanity with stool, output shows kneeling on floor
- White bra image: Source was leaning forward, output shows sitting on bed

### Issue: Body Type Influence
**Status:** PARTIALLY RESOLVED

Source model's thin body proportions still influence output despite body reference. Body appears healthier in V8 but not fully matching Starbright's reference.

### Issue: Hair Color Consistency
**Status:** PARTIALLY RESOLVED

Hair color improved in V8 (darker brown) but still not consistently dark brown across all images.

---

## WORKING SOLUTION: Kreator Flow Method (v9)

**Status:** RESOLVED - February 2, 2026

### The Breakthrough

After extensive testing, we discovered the **Kreator Flow prompt structure** that successfully:
- Preserves Starbright's face identity from face reference
- Preserves body proportions from body reference  
- Copies exact pose, outfit, and camera angle from source image

### Reference Image Order

**CRITICAL**: The order of references matters!
1. **reference1** (Figure 1): Face reference - `starbright_face_reference_v3.webp`
2. **reference2** (Figure 2): Body reference - `body_reference.webp`
3. **reference3** (Figure 3): Pose source image (the image to transform)

### Kreator Flow Prompt Template (v9.1 - Updated Feb 2, 2026)

```
A portrait of Starbright, using the EXACT pose from reference3: [DETAILED POSE DESCRIPTION].

Replace the face with facial features from reference1: [FACE DESCRIPTORS].
Replace the body with EXACT proportions from reference2: [BODY DESCRIPTORS].

CRITICAL: Do NOT use body proportions from reference3. The body MUST match reference2's proportions exactly.

KEEP from reference3: The exact body position, hand placement, camera angle, [BACKGROUND], [OUTFIT] outfit.

Photorealistic, high detail, sharp focus, 8K quality.
```

**Key improvement in v9.1**: Added "EXACT proportions" and "CRITICAL: Do NOT use body proportions from reference3" to prevent source model's body from overriding the A-cup reference.

### Starbright Identity Descriptors

**Face descriptors:**
```
hazel-brown eyes, full lips with cupid's bow, natural freckles across nose and cheeks, dark brown straight hair, soft oval jaw, high cheekbones
```

**Body descriptors:**
```
slim petite healthy build, natural A-cup, feminine proportions, fair skin
```

### Negative Prompt

```
Original influencer's face, blue eyes, green eyes, black hair, blonde hair, light hair, different face, wrong identity, large bust, big chest, curvy, busty, [standard body negative prompts]
```

**Key body negative terms**: "large bust, big chest, curvy, busty" - prevents source model's body from overriding A-cup reference.

### Example Working Prompt

For a source image with leaning forward pose, white bra, red shorts:

```
A portrait of Starbright, using the EXACT pose from reference3: woman leaning forward with torso bent, hands resting on thighs near knees, head tilted slightly looking up at camera.

Replace the face with facial features from reference1: hazel-brown eyes, full lips with cupid's bow, natural freckles across nose and cheeks, dark brown straight hair.
Replace the body with proportions from reference2: slim petite healthy build, natural A-cup.

KEEP from reference3: The exact body position, hand placement on thighs, camera angle from above, indoor room background, white bralette and red shorts with white stripe outfit.

Photorealistic, high detail, sharp focus, 8K quality.
```

### Key Insights

1. **Explicit separation**: Tell the model exactly what to KEEP vs REPLACE
2. **Precise pose description**: Describe the pose in detail (body position, hand placement, camera angle)
3. **Reference assignment**: Use "from reference1/2/3" language consistently
4. **Negative prompts**: Explicitly block the original influencer's features

### Service Method

Use `FalSeedreamService.transform_with_pose_source()`:

```python
result = await fal_service.transform_with_pose_source(
    pose_source_path="path/to/source/image.jpg",
    pose_description="leaning forward with hands on thighs, camera from above",
    outfit_description="white bralette and red shorts",
    background_description="indoor room with gray walls"
)
```

---

## Version History
- v1: Initial transformation with basic prompts
- v2: Added face reference conditioning
- v3: Added Grok background analysis, body reference, hair color enforcement
- v4: Stronger body reference, pure room backgrounds
- v5: Fixed multiple-person generation issue
- v6-v8: Hair color and photorealism improvements
- v9: KREATOR FLOW METHOD (Feb 2, 2026)
  - Explicit KEEP/REPLACE prompt structure
  - Reference order: face, body, pose source
  - Detailed pose descriptions
- **v9.1: KREATOR FLOW + STRONGER BODY** (Feb 2, 2026)
  - Added "EXACT proportions" to body replacement line
  - Added CRITICAL instruction: "Do NOT use body proportions from reference3"
  - Added body negative prompts: "large bust, big chest, curvy, busty"
  - Successfully prevents source model's body from overriding A-cup reference
