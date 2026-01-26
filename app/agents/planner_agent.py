"""
PlannerAgent - Daily content planning and task generation

Reads configuration and creates a daily task list for content generation
including style rotation, platform quotas, and scheduling.
"""

import logging
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.config import INFLUENCERS, InfluencerConfig
from app.pipeline_config import (
    get_pipeline_config, 
    STYLE_PROFILES,
    InfluencerPipelineConfig,
    StyleProfile
)

logger = logging.getLogger(__name__)


class GenerationTask(BaseModel):
    """A single content generation task"""
    task_id: str
    influencer_name: str
    influencer_handle: str
    platform: str
    style_profile: str
    pose: str
    outfit: str
    background: str
    mood: str
    scheduled_time: str
    subreddit: str = ""
    priority: int = 1


class DailyPlan(BaseModel):
    """Complete daily content plan"""
    plan_id: str
    date: str
    influencer_name: str
    total_tasks: int
    tasks_by_platform: Dict[str, int]
    tasks: List[GenerationTask]
    created_at: str


class PlannerAgent:
    """
    Plans daily content generation tasks for each influencer.
    
    Responsibilities:
    - Read quotas from config
    - Generate task list with style rotation
    - Schedule posts across the day
    - Assign subreddits for Reddit posts
    """
    
    def __init__(self):
        logger.info("PlannerAgent initialized")
    
    async def create_daily_plan(
        self,
        influencer: InfluencerConfig,
        date: datetime = None
    ) -> DailyPlan:
        """Create a complete daily plan for an influencer"""
        if date is None:
            date = datetime.now()
        
        handle = influencer.handle.replace("@", "").lower()
        config = get_pipeline_config(handle)
        
        logger.info(f"Creating daily plan for {influencer.name}")
        
        tasks = []
        task_counter = 0
        
        reddit_tasks = await self._create_platform_tasks(
            influencer=influencer,
            config=config,
            platform="reddit",
            count=config.quotas.reddit,
            date=date,
            task_offset=task_counter
        )
        tasks.extend(reddit_tasks)
        task_counter += len(reddit_tasks)
        
        twitter_tasks = await self._create_platform_tasks(
            influencer=influencer,
            config=config,
            platform="twitter",
            count=config.quotas.twitter,
            date=date,
            task_offset=task_counter
        )
        tasks.extend(twitter_tasks)
        task_counter += len(twitter_tasks)
        
        ig_tasks = await self._create_platform_tasks(
            influencer=influencer,
            config=config,
            platform="instagram_manual",
            count=config.quotas.instagram_manual,
            date=date,
            task_offset=task_counter
        )
        tasks.extend(ig_tasks)
        task_counter += len(ig_tasks)
        
        tiktok_tasks = await self._create_platform_tasks(
            influencer=influencer,
            config=config,
            platform="tiktok_manual",
            count=config.quotas.tiktok_manual,
            date=date,
            task_offset=task_counter
        )
        tasks.extend(tiktok_tasks)
        
        plan = DailyPlan(
            plan_id=f"plan_{handle}_{date.strftime('%Y%m%d_%H%M%S')}",
            date=date.strftime("%Y-%m-%d"),
            influencer_name=influencer.name,
            total_tasks=len(tasks),
            tasks_by_platform={
                "reddit": len(reddit_tasks),
                "twitter": len(twitter_tasks),
                "instagram_manual": len(ig_tasks),
                "tiktok_manual": len(tiktok_tasks)
            },
            tasks=tasks,
            created_at=datetime.now().isoformat()
        )
        
        logger.info(f"Daily plan created: {plan.total_tasks} tasks for {influencer.name}")
        return plan
    
    async def _create_platform_tasks(
        self,
        influencer: InfluencerConfig,
        config: InfluencerPipelineConfig,
        platform: str,
        count: int,
        date: datetime,
        task_offset: int
    ) -> List[GenerationTask]:
        """Create tasks for a specific platform"""
        tasks = []
        handle = influencer.handle.replace("@", "").lower()
        
        style_profiles = config.style_profiles if config.style_profiles else [
            STYLE_PROFILES.get("casual_lifestyle", list(STYLE_PROFILES.values())[0])
        ]
        
        posting_window = config.posting_window
        time_slots = self._distribute_times(
            count=count,
            start_hour=posting_window.start_hour,
            end_hour=posting_window.end_hour,
            date=date
        )
        
        subreddits = []
        if platform == "reddit" and config.target_subreddits:
            subreddits = [s.name for s in config.target_subreddits]
        
        for i in range(count):
            style = style_profiles[i % len(style_profiles)]
            
            pose = random.choice(style.poses)
            outfit = random.choice(style.outfits)
            background = random.choice(style.backgrounds)
            
            subreddit = ""
            if platform == "reddit" and subreddits:
                subreddit = subreddits[i % len(subreddits)]
            
            task = GenerationTask(
                task_id=f"task_{handle}_{platform}_{date.strftime('%Y%m%d')}_{task_offset + i:03d}",
                influencer_name=influencer.name,
                influencer_handle=influencer.handle,
                platform=platform,
                style_profile=style.name,
                pose=pose,
                outfit=outfit,
                background=background,
                mood=style.mood,
                scheduled_time=time_slots[i].isoformat() if i < len(time_slots) else time_slots[-1].isoformat(),
                subreddit=subreddit,
                priority=1 if platform in ["reddit", "twitter"] else 2
            )
            tasks.append(task)
        
        return tasks
    
    def _distribute_times(
        self,
        count: int,
        start_hour: int,
        end_hour: int,
        date: datetime
    ) -> List[datetime]:
        """Distribute posting times evenly across the day"""
        if count == 0:
            return []
        
        total_minutes = (end_hour - start_hour) * 60
        interval = total_minutes // max(count, 1)
        
        times = []
        for i in range(count):
            minutes_offset = i * interval + random.randint(0, min(interval // 2, 30))
            post_time = date.replace(
                hour=start_hour,
                minute=0,
                second=0,
                microsecond=0
            ) + timedelta(minutes=minutes_offset)
            times.append(post_time)
        
        return times
    
    async def get_generation_prompt(self, task: GenerationTask) -> str:
        """Build a generation prompt from a task"""
        prompt_parts = [
            f"photorealistic portrait of a young woman",
            f"{task.pose}",
            f"wearing {task.outfit}",
            f"in {task.background}",
            f"{task.mood} mood",
            "professional photography, natural lighting, high quality"
        ]
        return ", ".join(prompt_parts)
