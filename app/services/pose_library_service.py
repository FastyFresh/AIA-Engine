"""
Pose Library Service - Access alluring pose prompts for image generation
"""
import json
import random
from pathlib import Path
from typing import Optional, List, Dict

class PoseLibraryService:
    """Service to access and use the alluring pose library for image generation."""
    
    def __init__(self):
        self.library_path = Path("content/prompt_templates/alluring_pose_library.json")
        self.library = self._load_library()
    
    def _load_library(self) -> dict:
        """Load the pose library from JSON file."""
        if self.library_path.exists():
            with open(self.library_path, 'r') as f:
                return json.load(f)
        return {}
    
    def get_pose_categories(self) -> List[str]:
        """Get all available pose categories."""
        return list(self.library.get("poses", {}).keys())
    
    def get_poses_in_category(self, category: str) -> List[Dict]:
        """Get all poses in a specific category."""
        return self.library.get("poses", {}).get(category, [])
    
    def get_pose_by_name(self, name: str) -> Optional[Dict]:
        """Find a specific pose by name across all categories."""
        for category, poses in self.library.get("poses", {}).items():
            for pose in poses:
                if pose.get("name") == name:
                    return pose
        return None
    
    def get_random_pose(self, category: Optional[str] = None) -> Dict:
        """Get a random pose, optionally from a specific category."""
        if category:
            poses = self.get_poses_in_category(category)
        else:
            all_poses = []
            for cat_poses in self.library.get("poses", {}).values():
                all_poses.extend(cat_poses)
            poses = all_poses
        
        return random.choice(poses) if poses else {}
    
    def get_random_expression(self, mood: str = "seductive") -> str:
        """Get a random expression for a given mood."""
        expressions = self.library.get("expressions", {}).get(mood, [])
        return random.choice(expressions) if expressions else "alluring expression"
    
    def get_body_language_enhancers(self, count: int = 2) -> List[str]:
        """Get random body language enhancers."""
        enhancers = self.library.get("body_language_enhancers", [])
        return random.sample(enhancers, min(count, len(enhancers)))
    
    def get_hand_placement(self) -> str:
        """Get a random hand placement suggestion."""
        placements = self.library.get("posing_principles", {}).get("hand_placement", [])
        return random.choice(placements) if placements else ""
    
    def build_pose_prompt(
        self,
        pose_name: Optional[str] = None,
        category: Optional[str] = None,
        expression_mood: str = "seductive",
        include_enhancers: bool = True
    ) -> str:
        """
        Build a complete pose prompt string for image generation.
        
        Args:
            pose_name: Specific pose name to use, or None for random
            category: Category to pick random pose from
            expression_mood: Mood for expression (seductive, playful, intimate, confident)
            include_enhancers: Whether to add body language enhancers
            
        Returns:
            Complete pose prompt string
        """
        if pose_name:
            pose = self.get_pose_by_name(pose_name)
        elif category:
            pose = self.get_random_pose(category)
        else:
            pose = self.get_random_pose()
        
        if not pose:
            return "standing with confident alluring pose"
        
        prompt_parts = []
        
        prompt_parts.append(f"She is {pose.get('prompt', '')}")
        
        if pose.get("expression"):
            prompt_parts.append(f"with {pose['expression']}")
        else:
            expression = self.get_random_expression(expression_mood)
            prompt_parts.append(f"with {expression}")
        
        if include_enhancers:
            enhancers = self.get_body_language_enhancers(2)
            if enhancers:
                prompt_parts.append(f", {', '.join(enhancers)}")
        
        return " ".join(prompt_parts)
    
    def build_alluring_prompt(
        self,
        identity: str,
        outfit: str,
        background: str,
        pose_name: Optional[str] = None,
        pose_category: Optional[str] = None,
        expression_mood: str = "seductive"
    ) -> str:
        """
        Build a complete alluring image prompt with all components.
        
        Args:
            identity: Character identity description
            outfit: Clothing/outfit description
            background: Background/setting description
            pose_name: Specific pose name or None for random
            pose_category: Category to pick from if no specific pose
            expression_mood: Expression mood type
            
        Returns:
            Complete prompt ready for image generation
        """
        pose_prompt = self.build_pose_prompt(
            pose_name=pose_name,
            category=pose_category,
            expression_mood=expression_mood,
            include_enhancers=True
        )
        
        prompt = f"""ultra hyper-realistic photograph of a {identity}.
{pose_prompt}.
She is wearing {outfit}.
{background}.
Sensual boudoir photography style, soft glamorous lighting.
8K detail, natural skin texture with visible pores and freckles, professional fashion photography."""
        
        return prompt


STARBRIGHT_IDENTITY = """young woman with very pale porcelain skin, straight dark brown hair, 
warm olive-brown eyes, natural freckles across nose and cheeks, petite slim figure with small perky breasts, slender waist"""

LUNA_IDENTITY = """young woman with long straight pink hair, blue-green eyes, slim petite figure, 
natural beauty, smooth pale skin"""

LUXURY_LIVING_ROOM = "modern luxury living room with large windows, natural light, elegant furniture, neutral cream and beige tones"

BRIGHT_WHITE_BEDROOM = "bright minimalist white bedroom with large windows, natural daylight, white sheets and bedding"

COZY_BEDROOM = "cozy bedroom with soft warm lighting, plush bedding, intimate atmosphere"


def generate_alluring_starbright_prompt(
    outfit: str,
    pose_name: Optional[str] = None,
    pose_category: Optional[str] = None,
    background: str = LUXURY_LIVING_ROOM,
    expression_mood: str = "seductive"
) -> str:
    """
    Quick helper to generate an alluring Starbright prompt.
    
    Example:
        prompt = generate_alluring_starbright_prompt(
            outfit="black lace lingerie set",
            pose_category="kneeling",
            expression_mood="playful"
        )
    """
    service = PoseLibraryService()
    return service.build_alluring_prompt(
        identity=STARBRIGHT_IDENTITY,
        outfit=outfit,
        background=background,
        pose_name=pose_name,
        pose_category=pose_category,
        expression_mood=expression_mood
    )


if __name__ == "__main__":
    service = PoseLibraryService()
    
    print("=== Pose Library Service Demo ===\n")
    
    print("Categories:", service.get_pose_categories())
    print()
    
    print("Random standing pose prompt:")
    print(service.build_pose_prompt(category="standing"))
    print()
    
    print("Specific pose (kneeling_hands_together):")
    print(service.build_pose_prompt(pose_name="kneeling_hands_together", expression_mood="playful"))
    print()
    
    print("Full Starbright prompt:")
    prompt = generate_alluring_starbright_prompt(
        outfit="white lace lingerie set with garter belt",
        pose_category="lying_on_back"
    )
    print(prompt)
