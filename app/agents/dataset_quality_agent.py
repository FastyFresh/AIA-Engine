"""
DatasetQualityAgent - Compares generated images against reference images using Grok Vision.
Scores each image for identity consistency and provides approve/review/reject recommendations.
"""

import os
import base64
import httpx
from typing import Optional
from pydantic import BaseModel

class QualityScore(BaseModel):
    """Quality assessment result for a generated image."""
    score: int  # 0-100
    recommendation: str  # APPROVE, REVIEW, REJECT
    face_match: int  # 0-100
    hair_match: int  # 0-100
    body_match: int  # 0-100
    overall_identity: int  # 0-100
    issues: list[str]  # List of detected issues
    notes: str  # AI analysis notes

class DatasetQualityAgent:
    """
    Agent that uses Grok Vision to compare generated images against reference images
    and score them for identity consistency.
    """
    
    def __init__(self):
        self.xai_api_key = os.environ.get("XAI_API_KEY")
        self.reference_dir = "content/training/starbright"
        self.reference_images = [
            "content/training/starbright/ref_face.png",  # Face closeup reference
            "content/training/starbright/ref_halfbody.png",  # Half body with freckles
            "content/training/starbright/ref_upperbody.jpg",  # Upper body reference
            "content/training/starbright/ref_fullbody.png"  # Full body reference
        ]
        
        # Thresholds for recommendations
        self.approve_threshold = 85
        self.review_threshold = 60
    
    def _encode_image(self, image_path: str) -> Optional[str]:
        """Encode image to base64."""
        try:
            if not os.path.exists(image_path):
                return None
            with open(image_path, "rb") as f:
                return base64.standard_b64encode(f.read()).decode("utf-8")
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            return None
    
    def _get_media_type(self, path: str) -> str:
        """Get media type from file extension."""
        ext = path.lower().split('.')[-1]
        return {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'webp': 'image/webp',
            'gif': 'image/gif'
        }.get(ext, 'image/png')
    
    async def score_image(self, image_path: str) -> QualityScore:
        """
        Score a generated image against the reference images.
        
        Args:
            image_path: Path to the generated image to score
            
        Returns:
            QualityScore with detailed assessment
        """
        if not self.xai_api_key:
            return QualityScore(
                score=0,
                recommendation="REJECT",
                face_match=0,
                hair_match=0,
                body_match=0,
                overall_identity=0,
                issues=["XAI_API_KEY not configured"],
                notes="Cannot analyze without API key"
            )
        
        # Encode the generated image
        generated_b64 = self._encode_image(image_path)
        if not generated_b64:
            return QualityScore(
                score=0,
                recommendation="REJECT",
                face_match=0,
                hair_match=0,
                body_match=0,
                overall_identity=0,
                issues=["Could not load generated image"],
                notes=f"Failed to load: {image_path}"
            )
        
        # Encode reference images
        ref_images = []
        for ref_path in self.reference_images:
            ref_b64 = self._encode_image(ref_path)
            if ref_b64:
                ref_images.append({
                    "path": ref_path,
                    "data": ref_b64,
                    "type": self._get_media_type(ref_path)
                })
        
        if len(ref_images) < 2:
            return QualityScore(
                score=0,
                recommendation="REJECT",
                face_match=0,
                hair_match=0,
                body_match=0,
                overall_identity=0,
                issues=["Not enough reference images available"],
                notes="Need at least 2 reference images for comparison"
            )
        
        # Build the comparison prompt - EXTREMELY STRICT identity matching
        prompt = """You are a forensic facial recognition expert performing STRICT identity verification. A fan of "Starbright Monroe" must instantly recognize her - if there's ANY doubt, it's not her.

REFERENCE IMAGES show the TRUE Starbright Monroe. Study them CAREFULLY before scoring.

=== STARBRIGHT'S UNIQUE IDENTIFYING FEATURES (ALL MUST MATCH) ===

**CRITICAL IDENTIFIERS - automatic penalty if missing:**
1. FRECKLES: Distinct scattered freckles across nose bridge and upper cheeks - these are VISIBLE even in professional photos. If freckles are faint/missing = DEDUCT 20+ points from face_match
2. FACE SHAPE: Delicate oval-to-heart shape with NARROW jaw tapering to a refined chin. If face appears wider/rounder = DEDUCT 15+ points
3. LIPS: Full with PRONOUNCED cupid's bow, plump lower lip. If lips are thin or flat = DEDUCT 15+ points
4. NOSE: Refined, narrow bridge, small tip. If nose appears wider/larger = DEDUCT 10+ points

**SECONDARY IDENTIFIERS:**
5. EYES: Large hazel-green with dark lashes, slight almond shape, expressive
6. EYEBROWS: Natural arch, not too thick, dark brown
7. CHIN: Small, delicate, pointed - NOT round
8. CHEEKBONES: Soft, feminine, not prominent
9. HAIR: Long dark brown, straight to slight wave

=== GENERATED IMAGE TO SCORE (last image shown) ===

SCORING RULES - BE HARSH:
- Missing/faint freckles = face_match MAX 70
- Wrong face shape (too wide, round, square) = face_match MAX 65
- Wrong lip shape (thin, no cupid's bow) = face_match MAX 65
- Multiple issues = overall_identity MAX 55
- Would NOT be recognized as same person = overall_identity MAX 50
- Only 85+ if a fan would IMMEDIATELY say "that's Starbright"
- Only 90+ if nearly identical (twins)

COMPARISON CHECKLIST:
□ Are freckles clearly visible on nose/cheeks?
□ Is face shape narrow/heart-shaped (not round)?
□ Are lips full with defined cupid's bow?
□ Is nose refined and narrow?
□ Would this pass as the same person in a side-by-side?

Respond ONLY with JSON:
{
    "face_match": <0-100>,
    "hair_match": <0-100>,
    "body_match": <0-100>,
    "overall_identity": <0-100>,
    "issues": ["specific issue 1", "specific issue 2"],
    "notes": "2-3 sentence analysis - BE SPECIFIC about what differs"
}

THINK: Would a fan scrolling Twitter IMMEDIATELY recognize this as Starbright? If you hesitate = score below 75."""

        # Build messages with images
        content = []
        
        # Add reference images first
        for i, ref in enumerate(ref_images):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{ref['type']};base64,{ref['data']}"
                }
            })
        
        # Add the generated image last
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{self._get_media_type(image_path)};base64,{generated_b64}"
            }
        })
        
        # Add the prompt
        content.append({
            "type": "text",
            "text": prompt
        })
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.xai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-2-vision-1212",
                        "messages": [
                            {
                                "role": "user",
                                "content": content
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 500
                    }
                )
                
                if response.status_code != 200:
                    return QualityScore(
                        score=0,
                        recommendation="REJECT",
                        face_match=0,
                        hair_match=0,
                        body_match=0,
                        overall_identity=0,
                        issues=[f"API error: {response.status_code}"],
                        notes=response.text[:200]
                    )
                
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]
                
                # Parse the JSON response
                import json
                # Extract JSON from response (may have markdown formatting)
                json_str = ai_response
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                
                scores = json.loads(json_str.strip())
                
                # Calculate overall score (weighted average)
                overall_score = int(
                    scores.get("face_match", 0) * 0.4 +
                    scores.get("hair_match", 0) * 0.2 +
                    scores.get("body_match", 0) * 0.15 +
                    scores.get("overall_identity", 0) * 0.25
                )
                
                # Determine recommendation
                if overall_score >= self.approve_threshold:
                    recommendation = "APPROVE"
                elif overall_score >= self.review_threshold:
                    recommendation = "REVIEW"
                else:
                    recommendation = "REJECT"
                
                return QualityScore(
                    score=overall_score,
                    recommendation=recommendation,
                    face_match=scores.get("face_match", 0),
                    hair_match=scores.get("hair_match", 0),
                    body_match=scores.get("body_match", 0),
                    overall_identity=scores.get("overall_identity", 0),
                    issues=scores.get("issues", []),
                    notes=scores.get("notes", "")
                )
                
        except json.JSONDecodeError as e:
            return QualityScore(
                score=0,
                recommendation="REJECT",
                face_match=0,
                hair_match=0,
                body_match=0,
                overall_identity=0,
                issues=["Failed to parse AI response"],
                notes=f"JSON parse error: {str(e)}"
            )
        except Exception as e:
            return QualityScore(
                score=0,
                recommendation="REJECT",
                face_match=0,
                hair_match=0,
                body_match=0,
                overall_identity=0,
                issues=[f"Error during analysis: {str(e)}"],
                notes=str(e)
            )
    
    async def score_batch(self, image_paths: list[str]) -> dict[str, QualityScore]:
        """
        Score multiple images.
        
        Args:
            image_paths: List of paths to images to score
            
        Returns:
            Dictionary mapping image paths to their scores
        """
        results = {}
        for path in image_paths:
            results[path] = await self.score_image(path)
        return results
    
    def get_pending_images(self, persona: str = "starbright") -> list[str]:
        """Get list of generated images that haven't been scored yet."""
        training_dir = f"content/training/{persona}"
        pending = []
        
        if not os.path.exists(training_dir):
            return pending
        
        for filename in os.listdir(training_dir):
            if filename.startswith(f"{persona}_") and filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
                # Check if already has a score file
                score_file = os.path.join(training_dir, filename.replace(".png", "_score.json"))
                if not os.path.exists(score_file):
                    pending.append(os.path.join(training_dir, filename))
        
        return pending
    
    async def approve_image(self, image_path: str, persona: str = "starbright") -> bool:
        """Mark an image as approved for training."""
        try:
            import json
            score_file = image_path.replace(".png", "_score.json").replace(".jpg", "_score.json")
            
            # Create or update score file with approved status
            score_data = {"status": "approved", "manual": True}
            if os.path.exists(score_file):
                with open(score_file, "r") as f:
                    score_data = json.load(f)
            
            score_data["status"] = "approved"
            
            with open(score_file, "w") as f:
                json.dump(score_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error approving image: {e}")
            return False
    
    async def reject_image(self, image_path: str, delete: bool = False) -> bool:
        """Reject an image - either archive or delete it."""
        try:
            import shutil
            
            if delete:
                # Delete the image and associated files
                os.remove(image_path)
                txt_file = image_path.replace(".png", ".txt").replace(".jpg", ".txt")
                if os.path.exists(txt_file):
                    os.remove(txt_file)
                score_file = image_path.replace(".png", "_score.json").replace(".jpg", "_score.json")
                if os.path.exists(score_file):
                    os.remove(score_file)
            else:
                # Move to rejected folder
                rejected_dir = "content/training/rejected"
                os.makedirs(rejected_dir, exist_ok=True)
                
                filename = os.path.basename(image_path)
                shutil.move(image_path, os.path.join(rejected_dir, filename))
                
                # Move associated txt file if exists
                txt_file = image_path.replace(".png", ".txt").replace(".jpg", ".txt")
                if os.path.exists(txt_file):
                    shutil.move(txt_file, os.path.join(rejected_dir, filename.replace(".png", ".txt")))
            
            return True
        except Exception as e:
            print(f"Error rejecting image: {e}")
            return False
    
    def reset_scores(self, persona: str = "starbright") -> dict:
        """Reset all scores to allow re-analysis with updated criteria."""
        training_dir = f"content/training/{persona}"
        reset_count = 0
        
        if not os.path.exists(training_dir):
            return {"reset": 0, "message": "Training directory not found"}
        
        for filename in os.listdir(training_dir):
            if filename.endswith("_score.json"):
                score_path = os.path.join(training_dir, filename)
                try:
                    os.remove(score_path)
                    reset_count += 1
                except Exception as e:
                    print(f"Error deleting {score_path}: {e}")
        
        return {"reset": reset_count, "message": f"Reset {reset_count} score files for re-analysis"}
    
    def get_curation_stats(self, persona: str = "starbright") -> dict:
        """Get statistics about the curation process."""
        import json
        
        training_dir = f"content/training/{persona}"
        stats = {
            "total": 0,
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "review": 0,
            "target": 20
        }
        
        if not os.path.exists(training_dir):
            return stats
        
        for filename in os.listdir(training_dir):
            if not filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
                continue
            if filename.startswith("ref_"):
                continue  # Skip reference images
            
            stats["total"] += 1
            
            # Check for score file
            base = filename.rsplit(".", 1)[0]
            score_file = os.path.join(training_dir, f"{base}_score.json")
            
            if os.path.exists(score_file):
                try:
                    with open(score_file, "r") as f:
                        score_data = json.load(f)
                    status = score_data.get("status", "pending")
                    if status == "approved":
                        stats["approved"] += 1
                    elif status == "rejected":
                        stats["rejected"] += 1
                    elif status == "review":
                        stats["review"] += 1
                    else:
                        stats["pending"] += 1
                except:
                    stats["pending"] += 1
            else:
                stats["pending"] += 1
        
        return stats
