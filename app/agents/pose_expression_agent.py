"""
Pose & Expression Agent - LLM-powered head pose and facial expression variation
Uses Grok/XAI to analyze content context and suggest appropriate poses/expressions
"""
import os
import json
import random
import httpx
from typing import Optional, Dict, List
from pathlib import Path

XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_API_URL = "https://api.x.ai/v1/chat/completions"

POSE_LIBRARY = {
    "looking_at_camera": "looking directly at camera",
    "looking_away": "looking away from camera, candid",
    "head_tilted_left": "head tilted slightly to the left",
    "head_tilted_right": "head tilted slightly to the right",
    "looking_down": "looking down softly",
    "looking_up": "looking up with dreamy gaze",
    "profile_left": "profile view facing left",
    "profile_right": "profile view facing right",
    "over_shoulder": "looking over shoulder at camera",
    "three_quarter": "three-quarter view",
}

EXPRESSION_LIBRARY = {
    "confident_smile": "confident warm smile",
    "soft_smile": "soft subtle smile",
    "playful": "playful flirty expression",
    "serene": "serene peaceful expression",
    "sultry": "sultry intense gaze",
    "natural": "natural relaxed expression",
    "mysterious": "mysterious slight smile",
    "happy": "genuinely happy expression",
    "focused": "focused determined look",
    "dreamy": "dreamy thoughtful expression",
}

THEME_DEFAULTS = {
    "motivation_monday": {
        "poses": ["looking_at_camera", "focused", "three_quarter"],
        "expressions": ["confident_smile", "focused", "determined"]
    },
    "tease_tuesday": {
        "poses": ["over_shoulder", "looking_away", "head_tilted_right"],
        "expressions": ["playful", "sultry", "mysterious"]
    },
    "wellness_wednesday": {
        "poses": ["looking_up", "profile_left", "looking_at_camera"],
        "expressions": ["serene", "peaceful", "soft_smile"]
    },
    "thirsty_thursday": {
        "poses": ["looking_at_camera", "over_shoulder", "head_tilted_left"],
        "expressions": ["sultry", "confident_smile", "playful"]
    },
    "fanvue_friday": {
        "poses": ["looking_at_camera", "over_shoulder", "looking_away"],
        "expressions": ["sultry", "mysterious", "playful"]
    },
    "selfie_saturday": {
        "poses": ["looking_at_camera", "head_tilted_right", "three_quarter"],
        "expressions": ["happy", "natural", "soft_smile"]
    },
    "soft_sunday": {
        "poses": ["looking_down", "looking_away", "profile_right"],
        "expressions": ["serene", "dreamy", "soft_smile"]
    },
}

class PoseExpressionAgent:
    def __init__(self):
        self.history_file = Path("content/pose_history.json")
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text())
            except:
                pass
        return {"used_combinations": []}
    
    def _save_history(self):
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text(json.dumps(self.history, indent=2))
    
    def reset_weekly_history(self):
        self.history = {"used_combinations": []}
        self._save_history()
    
    async def get_pose_expression(
        self,
        theme: str,
        outfit: str,
        scene: str,
        content_type: str = "instagram",
        use_llm: bool = True
    ) -> Dict:
        """Get context-appropriate pose and expression using LLM"""
        
        if use_llm and XAI_API_KEY:
            try:
                result = await self._get_llm_suggestion(theme, outfit, scene, content_type)
                if result:
                    self._record_usage(result)
                    return result
            except Exception as e:
                print(f"LLM suggestion failed, using fallback: {e}")
        
        return self._get_fallback_suggestion(theme)
    
    async def _get_llm_suggestion(
        self,
        theme: str,
        outfit: str,
        scene: str,
        content_type: str
    ) -> Optional[Dict]:
        """Use Grok to suggest pose and expression"""
        
        recent_poses = [c.get("pose") for c in self.history.get("used_combinations", [])[-5:]]
        
        system_prompt = """You are a creative director for AI influencer content.
Given context about a photoshoot, suggest the best head pose and facial expression.

AVAILABLE POSES:
- looking_at_camera: direct eye contact
- looking_away: candid off-camera gaze  
- head_tilted_left/right: slight head tilt
- looking_down: soft downward gaze
- looking_up: dreamy upward look
- profile_left/right: side profile
- over_shoulder: looking back at camera
- three_quarter: angled view

AVAILABLE EXPRESSIONS:
- confident_smile: warm confident smile
- soft_smile: subtle gentle smile
- playful: flirty fun expression
- serene: peaceful calm look
- sultry: intense alluring gaze
- natural: relaxed authentic
- mysterious: enigmatic slight smile
- happy: genuine joy
- focused: determined look
- dreamy: thoughtful far-away look

Return ONLY valid JSON with this exact format:
{"pose": "pose_key", "expression": "expression_key", "prompt_snippet": "short phrase for image prompt"}"""
        
        user_prompt = f"""Content Theme: {theme}
Outfit: {outfit}
Scene: {scene}
Platform: {content_type}
Recent poses used (avoid repeating): {recent_poses}

Suggest the best pose and expression for this shot. Return JSON only."""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                XAI_API_URL,
                headers={
                    "Authorization": f"Bearer {XAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "grok-3-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                
                result = json.loads(content)
                
                if result.get("pose") in POSE_LIBRARY and result.get("expression") in EXPRESSION_LIBRARY:
                    return {
                        "pose": result["pose"],
                        "pose_text": POSE_LIBRARY[result["pose"]],
                        "expression": result["expression"],
                        "expression_text": EXPRESSION_LIBRARY[result["expression"]],
                        "prompt_snippet": result.get("prompt_snippet", ""),
                        "source": "llm"
                    }
        
        return None
    
    def _get_fallback_suggestion(self, theme: str) -> Dict:
        """Fallback to theme-based random selection"""
        theme_key = theme.lower().replace(" ", "_")
        defaults = THEME_DEFAULTS.get(theme_key, {
            "poses": list(POSE_LIBRARY.keys()),
            "expressions": list(EXPRESSION_LIBRARY.keys())
        })
        
        recent = [c.get("pose") for c in self.history.get("used_combinations", [])[-3:]]
        available_poses = [p for p in defaults["poses"] if p not in recent]
        if not available_poses:
            available_poses = defaults["poses"]
        
        pose = random.choice(available_poses)
        expression = random.choice(defaults["expressions"])
        
        result = {
            "pose": pose,
            "pose_text": POSE_LIBRARY.get(pose, pose),
            "expression": expression,
            "expression_text": EXPRESSION_LIBRARY.get(expression, expression),
            "prompt_snippet": f"{POSE_LIBRARY.get(pose, '')}, {EXPRESSION_LIBRARY.get(expression, '')}",
            "source": "fallback"
        }
        
        self._record_usage(result)
        return result
    
    def _record_usage(self, result: Dict):
        """Record pose/expression usage to avoid repetition"""
        self.history.setdefault("used_combinations", [])
        self.history["used_combinations"].append({
            "pose": result["pose"],
            "expression": result["expression"]
        })
        if len(self.history["used_combinations"]) > 50:
            self.history["used_combinations"] = self.history["used_combinations"][-20:]
        self._save_history()
    
    def build_prompt_with_pose(
        self,
        base_prompt: str,
        pose_data: Dict
    ) -> str:
        """Inject pose/expression into Seedream4 prompt"""
        snippet = pose_data.get("prompt_snippet", "")
        if not snippet:
            snippet = f"{pose_data.get('pose_text', '')}, {pose_data.get('expression_text', '')}"
        
        if "young woman model" in base_prompt:
            return base_prompt.replace(
                "young woman model",
                f"young woman model, {snippet}"
            )
        
        return f"{base_prompt}, {snippet}"


pose_expression_agent = PoseExpressionAgent()
