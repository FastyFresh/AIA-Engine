"""
PromptVariationService - Injects diversity into Seedream4 prompts
to prevent repetitive facial poses, expressions, and accessories.
"""
import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

ROTATION_FILE = Path("content/prompt_rotation_state.json")

POSE_CATALOG = [
    "full body shot from head to feet, standing pose, hand on hip, looking directly at camera",
    "full body shot from head to feet, arched back, looking over shoulder seductively",
    "full body shot from head to feet, one hand running through hair",
    "full body shot from head to feet, standing pose, hip cocked to side, chin slightly raised",
    "full body shot from head to feet, leaning forward showing curves",
    "full body shot from head to feet, side profile, accentuating figure",
    "full body shot from head to feet, stretching arms above head",
    "full body shot from head to feet, hand resting on thigh",
    "full body shot from head to feet, body angled with one leg forward",
    "full body shot from head to feet, sitting with legs crossed elegantly"
]

EXPRESSION_CATALOG = [
    "sultry bedroom eyes with parted lips",
    "seductive smirk with direct eye contact",
    "soft inviting gaze, lips slightly parted",
    "confident subtle gaze",
    "mysterious come-hither look",
    "relaxed natural expression",
    "intense smoldering gaze",
    "subtle knowing look",
    "sensual relaxed expression",
    "flirtatious sideways glance"
]

EARRING_CATALOG = [
    ("bare ears with no earrings", "no earrings visible, no ear jewelry"),
    ("small diamond stud earrings", "no hoop earrings, no dangling earrings, no drop earrings"),
    ("delicate gold drop earrings", "no stud earrings, no hoop earrings"),
    ("elegant pearl stud earrings", "no hoop earrings, no drop earrings, no dangling earrings"),
    ("tiny crystal stud earrings", "no hoop earrings, no dangling earrings, no drop earrings"),
    ("simple silver stud earrings", "no hoop earrings, no dangling earrings, no drop earrings"),
]

EXPRESSION_MODIFIERS = {
    "smiling": "confident alluring smile",
    "smirking": "seductive smirk with direct eye contact",
    "sultry": "sultry bedroom eyes with parted lips",
    "playful": "playful teasing expression",
    "serious": "intense smoldering gaze",
    "mysterious": "mysterious come-hither look",
    "confident": "confident alluring smile",
    "flirty": "flirtatious sideways glance",
    "seductive": "seductive smirk with direct eye contact",
}

POSE_MODIFIERS = {
    "looking back": "looking over shoulder seductively",
    "over shoulder": "looking over shoulder seductively",
    "side profile": "side profile, accentuating figure",
    "hand on hip": "hand on hip, looking directly at camera",
    "running through hair": "one hand running through hair",
    "leaning": "leaning forward showing curves",
    "stretching": "stretching arms above head",
    "sitting": "sitting with legs crossed elegantly",
}

OUTFIT_ENHANCEMENTS = {
    "skirt": "short mini skirt showing legs",
    "mini skirt": "tiny mini skirt showing legs",
    "dress": "short tight dress",
    "mini dress": "tiny form-fitting mini dress",
    "sundress": "short flowy sundress",
    "bodycon": "tight bodycon dress hugging curves",
    "crop top": "revealing crop top showing midriff",
    "top": "fitted low-cut top",
    "tank top": "tight tank top",
    "shorts": "tiny shorts showing legs",
    "jeans": "tight low-rise jeans",
    "pants": "form-fitting pants",
    "swimsuit": "high-cut swimsuit",
    "swimwear": "revealing high-cut swimwear",
    "loungewear": "silky revealing loungewear",
    "robe": "loosely tied silk robe",
    "pajamas": "silky short pajama set",
    "activewear": "tight form-fitting activewear",
    "yoga pants": "tight yoga pants accentuating curves",
    "leggings": "skin-tight leggings",
    "blouse": "low-cut fitted blouse",
    "shirt": "unbuttoned fitted shirt",
    "sweater": "off-shoulder sweater",
    "cardigan": "open cardigan over fitted top",
    "bodysuit": "form-fitting bodysuit hugging curves",
    "lingerie": "revealing lingerie",
    "bra": "lacy bra",
    "underwear": "lacy underwear",
    "panties": "lacy panties",
    "thong": "revealing thong",
}

def enhance_outfit_prompt(outfit_text: str) -> str:
    """
    Enhance outfit descriptions to be more provocative and alluring.
    Preserves color words from the original.
    """
    if not outfit_text:
        return outfit_text
    
    import re
    
    colors = [
        "red", "blue", "green", "yellow", "purple", "pink", "black", "white",
        "orange", "gold", "silver", "emerald", "ruby", "sapphire", "burgundy",
        "navy", "crimson", "coral", "teal", "maroon", "lavender", "turquoise",
        "beige", "cream", "ivory", "nude", "tan", "brown", "grey", "gray"
    ]
    
    found_colors = []
    outfit_lower = outfit_text.lower()
    for color in colors:
        if re.search(r'\b' + color + r'\b', outfit_lower):
            found_colors.append(color)
    
    enhanced = outfit_lower
    
    for keyword, replacement in OUTFIT_ENHANCEMENTS.items():
        if keyword in enhanced and replacement.lower() not in enhanced:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            enhanced = re.sub(pattern, replacement, enhanced, count=1)
    
    if found_colors:
        color_str = " ".join(found_colors)
        if not any(c in enhanced for c in found_colors):
            enhanced = f"{color_str} {enhanced}"
    
    return enhanced


class PromptVariationService:
    def __init__(self):
        self._lock_file = Path("content/.prompt_rotation.lock")
        self.rotation_state = self._load_rotation_state()
    
    def _load_rotation_state(self) -> Dict:
        if ROTATION_FILE.exists():
            try:
                with open(ROTATION_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load rotation state: {e}")
        return {"last_pose_idx": -1, "last_expression_idx": -1, "last_earring_idx": -1, "history": []}
    
    def _save_rotation_state(self, skip_lock: bool = False):
        import fcntl
        ROTATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        if skip_lock:
            try:
                with open(ROTATION_FILE, "w") as f:
                    json.dump(self.rotation_state, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to save rotation state: {e}")
        else:
            self._lock_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(self._lock_file, "w") as lock:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                    try:
                        with open(ROTATION_FILE, "w") as f:
                            json.dump(self.rotation_state, f, indent=2)
                    finally:
                        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            except Exception as e:
                logger.warning(f"Failed to save rotation state: {e}")
    
    def extract_cues(self, narrative: str) -> Tuple[Optional[str], Optional[str]]:
        narrative_lower = narrative.lower()
        
        pose_cue = None
        for keyword, modifier in POSE_MODIFIERS.items():
            if keyword in narrative_lower:
                pose_cue = modifier
                break
        
        expression_cue = None
        for keyword, modifier in EXPRESSION_MODIFIERS.items():
            if keyword in narrative_lower:
                expression_cue = modifier
                break
        
        return pose_cue, expression_cue
    
    def get_next_variation(self, narrative: str = "") -> Dict[str, str]:
        import fcntl
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self._lock_file, "w") as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                try:
                    self.rotation_state = self._load_rotation_state()
                    result = self._compute_variation(narrative)
                    self._save_rotation_state(skip_lock=True)
                    return result
                finally:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            logger.warning(f"Lock failed, computing without lock: {e}")
            return self._compute_variation(narrative)
    
    def _compute_variation(self, narrative: str) -> Dict[str, str]:
        pose_cue, expression_cue = self.extract_cues(narrative)
        
        last_pose = self.rotation_state.get("last_pose_idx", -1)
        available_poses = list(range(len(POSE_CATALOG)))
        if last_pose in available_poses and len(available_poses) > 1:
            available_poses.remove(last_pose)
        pose_idx = random.choice(available_poses)
        base_pose = POSE_CATALOG[pose_idx]
        self.rotation_state["last_pose_idx"] = pose_idx
        
        if pose_cue:
            conflicting_phrases = [
                "hand on hip",
                "looking directly at camera",
                "arched back",
                "looking over shoulder",
                "running through hair",
                "hip cocked",
                "chin slightly raised",
                "leaning forward",
                "showing curves",
                "side profile",
                "accentuating figure",
                "stretching arms",
                "hand resting on thigh",
                "body angled",
                "one leg forward",
                "sitting with legs crossed"
            ]
            cleaned_pose = base_pose
            for phrase in conflicting_phrases:
                cleaned_pose = cleaned_pose.replace(f", {phrase}", "")
                cleaned_pose = cleaned_pose.replace(phrase, "")
            cleaned_pose = cleaned_pose.strip().rstrip(",").strip()
            if cleaned_pose:
                pose = f"{cleaned_pose}, {pose_cue}"
            else:
                pose = f"full body pose, {pose_cue}"
        else:
            pose = base_pose
        
        last_expr = self.rotation_state.get("last_expression_idx", -1)
        available_expr = list(range(len(EXPRESSION_CATALOG)))
        if last_expr in available_expr and len(available_expr) > 1:
            available_expr.remove(last_expr)
        expr_idx = random.choice(available_expr)
        
        if expression_cue:
            expression = expression_cue
        else:
            expression = EXPRESSION_CATALOG[expr_idx]
        self.rotation_state["last_expression_idx"] = expr_idx
        
        last_earring = self.rotation_state.get("last_earring_idx", -1)
        available_earrings = list(range(len(EARRING_CATALOG)))
        if last_earring in available_earrings and len(available_earrings) > 1:
            available_earrings.remove(last_earring)
        earring_idx = random.choice(available_earrings)
        earring_positive, earring_negative = EARRING_CATALOG[earring_idx]
        self.rotation_state["last_earring_idx"] = earring_idx
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "pose": pose,
            "expression": expression,
            "earring": earring_positive
        }
        self.rotation_state.setdefault("history", []).append(history_entry)
        if len(self.rotation_state["history"]) > 20:
            self.rotation_state["history"] = self.rotation_state["history"][-20:]
        
        return {
            "pose": pose,
            "expression": expression,
            "earring_positive": earring_positive,
            "earring_negative": earring_negative
        }
    
    def get_variation_history(self) -> List[Dict]:
        return self.rotation_state.get("history", [])


prompt_variation_service = PromptVariationService()
