"""
PromptTestingAgent - Systematic prompt optimization for character consistency.

Uses Grok Vision to compare generated images against reference images,
scoring face and body consistency to find optimal prompt templates.
"""

import os
import json
import base64
import httpx
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class ConsistencyScore:
    face_match: int  # 0-100
    body_match: int  # 0-100
    hair_match: int  # 0-100
    overall_identity: int  # 0-100
    recommendation: str  # APPROVE, REVIEW, REJECT
    details: str


@dataclass 
class PromptTestResult:
    prompt_name: str
    prompt_template: str
    image_path: str
    score: ConsistencyScore
    timestamp: str
    seed: int
    generation_time_seconds: float


class PromptTestingAgent:
    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        self.xai_api_key = os.getenv("XAI_API_KEY")
        self.face_ref_path = "attached_assets/face_reference_image,_Starbright18_1765331888088.webp"
        self.body_ref_path = "attached_assets/starbright_body_reference_image_1765331888089.png"
        self.output_dir = Path("content/prompt_optimization")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.output_dir / "optimization_results.json"
        
    def _encode_image(self, path: str) -> str:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        ext = Path(path).suffix.lower()
        mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
        return f"data:{mime};base64,{data}"
    
    def score_image_with_grok(self, generated_image_path: str) -> ConsistencyScore:
        if not self.xai_api_key:
            return ConsistencyScore(
                face_match=0, body_match=0, hair_match=0, overall_identity=0,
                recommendation="ERROR", details="XAI_API_KEY not set"
            )
        
        generated_b64 = self._encode_image(generated_image_path)
        face_ref_b64 = self._encode_image(self.face_ref_path)
        body_ref_b64 = self._encode_image(self.body_ref_path)
        
        prompt = """You are an expert at comparing AI-generated images for character consistency.

Compare the GENERATED IMAGE against the FACE REFERENCE and BODY REFERENCE images.

Score each aspect from 0-100:
1. FACE_MATCH: How well does the face match? Consider: face shape, eyes, nose, lips, freckles, overall facial structure
2. BODY_MATCH: How well does the body match? Consider: body proportions, waist size, hip width, leg length, overall build
3. HAIR_MATCH: How well does the hair match? Consider: color, length, style, texture
4. OVERALL_IDENTITY: Overall, is this the same person?

Provide your response in this exact JSON format:
{
    "face_match": <0-100>,
    "body_match": <0-100>,
    "hair_match": <0-100>,
    "overall_identity": <0-100>,
    "recommendation": "<APPROVE if overall >= 85, REVIEW if 60-84, REJECT if < 60>",
    "details": "<brief explanation of what matches or differs>"
}

IMPORTANT: Focus especially on BODY proportions - waist-to-hip ratio, leg length relative to torso, overall slimness."""

        try:
            response = httpx.post(
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
                            "content": [
                                {"type": "text", "text": "FACE REFERENCE:"},
                                {"type": "image_url", "image_url": {"url": face_ref_b64}},
                                {"type": "text", "text": "BODY REFERENCE:"},
                                {"type": "image_url", "image_url": {"url": body_ref_b64}},
                                {"type": "text", "text": "GENERATED IMAGE TO SCORE:"},
                                {"type": "image_url", "image_url": {"url": generated_b64}},
                                {"type": "text", "text": prompt}
                            ]
                        }
                    ],
                    "temperature": 0.1
                },
                timeout=60
            )
            
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                score_data = json.loads(content[json_start:json_end])
                return ConsistencyScore(
                    face_match=score_data.get("face_match", 0),
                    body_match=score_data.get("body_match", 0),
                    hair_match=score_data.get("hair_match", 0),
                    overall_identity=score_data.get("overall_identity", 0),
                    recommendation=score_data.get("recommendation", "REVIEW"),
                    details=score_data.get("details", "")
                )
        except Exception as e:
            return ConsistencyScore(
                face_match=0, body_match=0, hair_match=0, overall_identity=0,
                recommendation="ERROR", details=str(e)
            )
        
        return ConsistencyScore(
            face_match=0, body_match=0, hair_match=0, overall_identity=0,
            recommendation="ERROR", details="Failed to parse response"
        )
    
    def generate_image(self, prompt: str, name: str, seed: int = 42, 
                       body_first: bool = True) -> tuple[str, float]:
        face_uri = self._encode_image(self.face_ref_path)
        body_uri = self._encode_image(self.body_ref_path)
        
        image_order = [body_uri, face_uri] if body_first else [face_uri, body_uri]
        
        start_time = time.time()
        
        response = httpx.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {self.replicate_token}",
                "Content-Type": "application/json"
            },
            json={
                "version": "cf7d431991436f19d1c8dad83fe463c729c816d7a21056c5105e75c84a0aa7e9",
                "input": {
                    "prompt": prompt,
                    "image_input": image_order,
                    "size": "2K",
                    "aspect_ratio": "9:16",
                    "enhance_prompt": False,
                    "seed": seed
                }
            },
            timeout=60
        )
        
        result = response.json()
        pred_id = result.get("id")
        
        if not pred_id:
            raise Exception(f"Failed to start prediction: {result}")
        
        for _ in range(60):
            time.sleep(3)
            check = httpx.get(
                f"https://api.replicate.com/v1/predictions/{pred_id}",
                headers={"Authorization": f"Token {self.replicate_token}"},
                timeout=30
            )
            status_data = check.json()
            status = status_data.get("status")
            
            if status == "succeeded":
                output = status_data.get("output", [])
                url = output[0] if isinstance(output, list) else output
                img = httpx.get(url, timeout=60)
                save_path = self.output_dir / f"{name}.png"
                with open(save_path, "wb") as f:
                    f.write(img.content)
                gen_time = time.time() - start_time
                return str(save_path), gen_time
            elif status in ["failed", "canceled"]:
                raise Exception(f"Prediction failed: {status_data.get('error')}")
        
        raise Exception("Prediction timed out")
    
    def test_prompt(self, prompt_name: str, prompt_template: str, 
                    seed: int = 42, body_first: bool = True) -> PromptTestResult:
        print(f"Testing prompt: {prompt_name}")
        
        image_path, gen_time = self.generate_image(
            prompt_template, prompt_name, seed, body_first
        )
        print(f"  Generated in {gen_time:.1f}s: {image_path}")
        
        print(f"  Scoring with Grok Vision...")
        score = self.score_image_with_grok(image_path)
        print(f"  Face: {score.face_match}, Body: {score.body_match}, Overall: {score.overall_identity}")
        print(f"  Recommendation: {score.recommendation}")
        
        result = PromptTestResult(
            prompt_name=prompt_name,
            prompt_template=prompt_template,
            image_path=image_path,
            score=score,
            timestamp=datetime.now().isoformat(),
            seed=seed,
            generation_time_seconds=gen_time
        )
        
        self._save_result(result)
        
        return result
    
    def _save_result(self, result: PromptTestResult):
        results = []
        if self.results_file.exists():
            with open(self.results_file) as f:
                results = json.load(f)
        
        results.append({
            "prompt_name": result.prompt_name,
            "prompt_template": result.prompt_template,
            "image_path": result.image_path,
            "score": asdict(result.score),
            "timestamp": result.timestamp,
            "seed": result.seed,
            "generation_time_seconds": result.generation_time_seconds
        })
        
        with open(self.results_file, "w") as f:
            json.dump(results, f, indent=2)
    
    def run_optimization_batch(self, prompt_variations: list[dict]) -> list[PromptTestResult]:
        results = []
        for variation in prompt_variations:
            result = self.test_prompt(
                prompt_name=variation["name"],
                prompt_template=variation["prompt"],
                seed=variation.get("seed", 42),
                body_first=variation.get("body_first", True)
            )
            results.append(result)
        
        results.sort(key=lambda x: x.score.body_match, reverse=True)
        
        print("\n=== OPTIMIZATION RESULTS (sorted by body match) ===")
        for r in results:
            print(f"{r.prompt_name}: Body={r.score.body_match}, Face={r.score.face_match}, Overall={r.score.overall_identity} [{r.score.recommendation}]")
        
        return results
    
    def get_best_prompt(self) -> Optional[dict]:
        if not self.results_file.exists():
            return None
        
        with open(self.results_file) as f:
            results = json.load(f)
        
        if not results:
            return None
        
        best = max(results, key=lambda x: (x["score"]["body_match"] + x["score"]["face_match"]) / 2)
        return best


if __name__ == "__main__":
    agent = PromptTestingAgent()
    
    prompt_variations = [
        {
            "name": "opt_v1_baseline",
            "prompt": "Full-body view, head-to-toe. Realistic skin, 18-19 years old, directly facing the camera, wearing light blue one-piece yoga suit, arms to sides, slim hips. Petite and slender. Neutral white background.",
            "body_first": True
        },
        {
            "name": "opt_v2_explicit_proportions",
            "prompt": "Full-body photograph showing entire figure head to feet. Match exact body proportions: narrow waist, slim hips, long slender legs, petite frame. 18-19 years old woman, standing straight facing camera, arms at sides, wearing light blue one-piece yoga suit. White studio background.",
            "body_first": True
        },
        {
            "name": "opt_v3_measurement_style",
            "prompt": "Full-body view head to toe. Young woman 18-19, waist-hip ratio 0.7, long legs, narrow shoulders, slim build. Standing facing camera, light blue one-piece yoga suit, arms relaxed. White background.",
            "body_first": True
        },
        {
            "name": "opt_v4_negative_constraints",
            "prompt": "Full-body view head to toe. 18-19 years old, very slim waist, narrow hips, long legs, petite build. Standing straight, arms at sides, light blue one-piece yoga suit. White background. NOT curvy, NOT wide hips, NOT muscular.",
            "body_first": True
        },
    ]
    
    results = agent.run_optimization_batch(prompt_variations)
    
    best = agent.get_best_prompt()
    if best:
        print(f"\nBest prompt: {best['prompt_name']}")
        print(f"Body match: {best['score']['body_match']}")
        print(f"Template: {best['prompt_template'][:100]}...")
