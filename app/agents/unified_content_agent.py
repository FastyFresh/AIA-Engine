"""
Unified Content Agent - Multi-influencer content generation orchestrator

Combines:
- LLM-powered pose/expression selection (PoseExpressionAgent)
- Theme-appropriate background selection (BackgroundAgent)
- 3-reference Seedream4 generation via Seedream4Service
- Safety-conscious prompt filtering via PromptSafetyFilter

Supports multiple influencers with configurable reference images and output paths.
"""
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import logging

from app.agents.pose_expression_agent import pose_expression_agent
from app.agents.background_agent import background_agent
from app.services.seedream4_service import Seedream4Service
from app.services.prompt_safety_filter import PromptSafetyFilter
from app.services.prompt_builder import PromptBuilder, INFLUENCER_IDENTITIES

logger = logging.getLogger(__name__)


INFLUENCER_CONFIG = {
    "starbright_monroe": {
        "name": "Starbright Monroe",
        "face_ref": INFLUENCER_IDENTITIES["starbright_monroe"]["face_ref"],
        "body_ref": INFLUENCER_IDENTITIES["starbright_monroe"]["body_ref"],
        "output_dir": INFLUENCER_IDENTITIES["starbright_monroe"]["output_dir"],
        "identity": f"hyperrealistic beautiful young woman, {INFLUENCER_IDENTITIES['starbright_monroe']['identity']}"
    },
    "luna_vale": {
        "name": "Luna Vale",
        "face_ref": INFLUENCER_IDENTITIES["luna_vale"]["face_ref"],
        "body_ref": INFLUENCER_IDENTITIES["luna_vale"]["body_ref"],
        "output_dir": INFLUENCER_IDENTITIES["luna_vale"]["output_dir"],
        "identity": f"hyperrealistic beautiful young woman, {INFLUENCER_IDENTITIES['luna_vale']['identity']}"
    }
}


class UnifiedContentAgent:
    """
    Multi-influencer content generation orchestrator.
    
    Delegates image generation to Seedream4Service (Replicate fallback) while managing
    pose, expression, and background selection via specialized agents.
    
    Note: For primary image generation, use FalSeedreamService directly.
    This agent uses Seedream4Service as it was designed for multi-reference generation.
    """
    
    def __init__(self):
        self.pose_agent = pose_expression_agent
        self.background_agent = background_agent
        self.seedream_service = Seedream4Service()
        self._influencer_cache: Dict[str, Dict] = {}
    
    def get_influencer_config(self, influencer_id: str) -> Dict:
        """Get configuration for an influencer"""
        if influencer_id not in INFLUENCER_CONFIG:
            raise ValueError(f"Unknown influencer: {influencer_id}. Available: {list(INFLUENCER_CONFIG.keys())}")
        return INFLUENCER_CONFIG[influencer_id]
    
    def list_influencers(self) -> List[str]:
        """List available influencer IDs"""
        return list(INFLUENCER_CONFIG.keys())
    
    async def generate_content(
        self,
        influencer_id: str,
        theme: str,
        outfit: str,
        time_of_day: Optional[str] = None,
        use_background_ref: bool = True,
        filename: Optional[str] = None,
        max_retries: int = 3
    ) -> Dict:
        """
        Generate a single piece of content for a specific influencer.
        
        Uses PromptSafetyFilter to sanitize prompts before generation.
        Implements retry logic with progressively safer alternatives on failure.
        
        Args:
            influencer_id: ID of the influencer (e.g., "starbright_monroe", "luna_vale")
            theme: Content theme (e.g., "motivation_monday", "thirsty_thursday")
            outfit: What the model is wearing
            time_of_day: "day", "night", or "golden_hour"
            use_background_ref: Whether to use background image as 3rd reference
            filename: Output filename (auto-generated if not provided)
            max_retries: Maximum retry attempts with safer alternatives
        
        Returns:
            Dict with generation result and metadata
        """
        config = self.get_influencer_config(influencer_id)
        output_dir = Path(config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        safe_outfit = PromptSafetyFilter.sanitize_outfit(outfit)
        if safe_outfit != outfit.lower():
            logger.info(f"Safety filter: '{outfit}' → '{safe_outfit}'")
        
        alternatives = PromptSafetyFilter.get_progressive_alternatives(outfit)
        
        pose_data = await self.pose_agent.get_pose_expression(
            theme=theme,
            outfit=safe_outfit,
            scene=theme,
            content_type="twitter"
        )
        
        bg_data = self.background_agent.get_background_for_theme(
            theme=theme,
            time_of_day=time_of_day
        )
        
        pose_text = pose_data.get("pose_text", "looking at camera")
        expression_text = pose_data.get("expression_text", "natural expression")
        bg_description = bg_data.get("description", "") if bg_data else ""
        bg_ref_path = bg_data.get("path") if use_background_ref and bg_data else None
        
        last_error = None
        used_outfit = safe_outfit
        prompt = ""
        
        for attempt, alt_outfit in enumerate(alternatives[:max_retries]):
            is_valid, validation_error = PromptSafetyFilter.validate_prompt(alt_outfit)
            if not is_valid:
                logger.warning(f"Skipping invalid alternative: {alt_outfit} - {validation_error}")
                continue
            
            prompt = f"POSE DIRECTION: The model MUST be {pose_text} with {expression_text}. Hyperrealistic magazine-quality fashion photography, stunning full body portrait, {config['identity']}, wearing {alt_outfit}, {bg_description}, 8k ultra HD, photorealistic skin texture with subtle imperfections, cinematic lighting, professional studio quality, sharp focus, alluring and captivating mood, the pose is critical - model must follow the pose direction exactly"
            
            is_prompt_valid, prompt_error = PromptSafetyFilter.validate_prompt(prompt)
            if not is_prompt_valid:
                logger.warning(f"Prompt validation failed: {prompt_error}")
                continue
            
            if attempt > 0:
                logger.info(f"Retry {attempt}/{max_retries}: Using alternative outfit '{alt_outfit}'")
            
            result = await self.seedream_service.generate_with_background(
                prompt=prompt,
                face_ref=config["face_ref"],
                body_ref=config["body_ref"],
                background_ref=bg_ref_path,
                aspect_ratio="9:16",
                filename_prefix=influencer_id
            )
            
            if result.get("status") == "success":
                used_outfit = alt_outfit
                break
            
            last_error = result.get("error", "Generation failed")
            
            if "flagged" in last_error.lower() or "sexual" in last_error.lower() or "content" in last_error.lower():
                logger.warning(f"Content flagged, trying safer alternative...")
                continue
            else:
                break
        else:
            return {
                "success": False,
                "error": last_error or "All retry attempts failed",
                "influencer": influencer_id,
                "original_outfit": outfit,
                "attempted_alternatives": alternatives[:max_retries]
            }
        
        if result.get("status") != "success":
            return {
                "success": False, 
                "error": result.get("error", "Generation failed"),
                "influencer": influencer_id
            }
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{theme}_{timestamp}.png"
        
        source_path = Path(result.get("image_path", ""))
        if source_path.exists():
            dest_path = output_dir / filename
            dest_path.write_bytes(source_path.read_bytes())
            final_path = str(dest_path)
        else:
            final_path = result.get("image_path", "")
        
        return {
            "success": True,
            "path": final_path,
            "filename": filename,
            "influencer": influencer_id,
            "theme": theme,
            "outfit": used_outfit,
            "original_outfit": outfit if used_outfit != outfit.lower() else None,
            "pose": pose_data,
            "pose_instruction": f"{pose_text} with {expression_text}",
            "background": bg_data,
            "prompt": prompt,
            "refs_used": 3 if bg_ref_path else 2,
            "safety_filtered": used_outfit != outfit.lower()
        }
    
    async def generate_weekly_content(
        self,
        influencer_id: str,
        content_plan: List[Dict],
        use_background_ref: bool = True
    ) -> List[Dict]:
        """
        Generate a full week of content for a specific influencer.
        
        Args:
            influencer_id: ID of the influencer
            content_plan: List of dicts with theme, outfit, time_of_day, filename
            use_background_ref: Whether to use background references
        
        Returns:
            List of generation results
        """
        results = []
        
        self.pose_agent.reset_weekly_history()
        self.background_agent.reset_daily_usage()
        
        config = self.get_influencer_config(influencer_id)
        logger.info(f"Starting weekly content generation for {config['name']}")
        
        for item in content_plan:
            theme = item.get("theme", "general")
            outfit = item.get("outfit", "casual outfit")
            
            result = await self.generate_content(
                influencer_id=influencer_id,
                theme=theme,
                outfit=outfit,
                time_of_day=item.get("time_of_day"),
                use_background_ref=use_background_ref,
                filename=item.get("filename")
            )
            results.append(result)
            
            if result.get("success"):
                pose_info = result.get('pose', {})
                pose_name = pose_info.get('pose', 'unknown') if pose_info else 'unknown'
                bg_info = result.get('background', {})
                bg_name = bg_info.get('id', 'none') if bg_info else 'none'
                logger.info(f"Generated: {result.get('filename', 'unknown')} - Pose: {pose_name}, BG: {bg_name}")
            else:
                logger.warning(f"Failed: {item.get('filename', 'unknown')} - {result.get('error')}")
        
        return results
    
    async def generate_for_all_influencers(
        self,
        content_plan: List[Dict],
        use_background_ref: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Generate content for all configured influencers.
        
        Args:
            content_plan: Content plan to apply to all influencers
            use_background_ref: Whether to use background references
        
        Returns:
            Dict mapping influencer_id to list of generation results
        """
        all_results = {}
        
        for influencer_id in INFLUENCER_CONFIG.keys():
            results = await self.generate_weekly_content(
                influencer_id=influencer_id,
                content_plan=content_plan,
                use_background_ref=use_background_ref
            )
            all_results[influencer_id] = results
        
        return all_results


unified_content_agent = UnifiedContentAgent()
