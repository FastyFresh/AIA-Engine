"""
Content Calendar Agent - AI-powered themed content scheduling

Generates weekly/monthly content calendars with:
- Theme-based organization (e.g., Motivation Monday, Thirsty Thursday)
- Optimal posting times based on audience engagement
- Variety in content types (full-body, close-up, lifestyle)
- Integration with hero images and micro-loop generation
"""

import os
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

CONTENT_THEMES = {
    "starbright_monroe": {
        "monday": {
            "theme": "Motivation Monday",
            "vibe": "energetic, fresh start, positive",
            "suggested_outfits": ["activewear", "casual chic", "athleisure"],
            "suggested_settings": ["gym", "morning light bedroom", "yoga studio"],
            "content_type": "full-body",
            "best_times": ["7:00 AM", "12:00 PM", "6:00 PM"]
        },
        "tuesday": {
            "theme": "Tease Tuesday",
            "vibe": "playful, flirty, mysterious",
            "suggested_outfits": ["lingerie", "silk robe", "oversized shirt"],
            "suggested_settings": ["bedroom", "bathroom mirror", "soft lighting"],
            "content_type": "upper-body",
            "best_times": ["9:00 PM", "11:00 PM"]
        },
        "wednesday": {
            "theme": "Wellness Wednesday",
            "vibe": "healthy, natural, glowing",
            "suggested_outfits": ["yoga wear", "sports bra", "minimal"],
            "suggested_settings": ["spa", "natural outdoor", "clean studio"],
            "content_type": "lifestyle",
            "best_times": ["8:00 AM", "5:00 PM"]
        },
        "thursday": {
            "theme": "Thirsty Thursday",
            "vibe": "sultry, confident, bold",
            "suggested_outfits": ["bikini", "bodysuit", "curve-hugging dress"],
            "suggested_settings": ["pool", "beach sunset", "hotel room"],
            "content_type": "full-body",
            "best_times": ["8:00 PM", "10:00 PM", "11:30 PM"]
        },
        "friday": {
            "theme": "Fanvue Friday",
            "vibe": "exclusive, teasing, direct CTA",
            "suggested_outfits": ["special lingerie", "red/black themed"],
            "suggested_settings": ["bedroom", "studio", "luxury setting"],
            "content_type": "upper-body",
            "best_times": ["9:00 PM", "11:00 PM"]
        },
        "saturday": {
            "theme": "Selfie Saturday",
            "vibe": "casual, relatable, personal",
            "suggested_outfits": ["casual home wear", "cozy", "natural"],
            "suggested_settings": ["home", "mirror selfie", "natural light"],
            "content_type": "close-up",
            "best_times": ["11:00 AM", "3:00 PM", "8:00 PM"]
        },
        "sunday": {
            "theme": "Soft Sunday",
            "vibe": "relaxed, intimate, warm",
            "suggested_outfits": ["loungewear", "silk pajamas", "minimal"],
            "suggested_settings": ["bed", "couch", "morning vibes"],
            "content_type": "lifestyle",
            "best_times": ["10:00 AM", "2:00 PM", "7:00 PM"]
        }
    }
}

POSTING_FREQUENCY = {
    "conservative": 1,
    "moderate": 2,
    "aggressive": 3,
    "maximum": 4
}


class ContentCalendarAgent:
    """AI-powered content calendar generation with themed scheduling"""
    
    def __init__(self, influencer: str = "starbright_monroe"):
        self.influencer = influencer
        self.xai_api_key = os.getenv("XAI_API_KEY")
        self.themes = CONTENT_THEMES.get(influencer, CONTENT_THEMES["starbright_monroe"])
        self.calendar_path = Path(f"content/calendars/{influencer}")
        self.calendar_path.mkdir(parents=True, exist_ok=True)
        self.hero_path = Path(f"content/references/{influencer}/hero")
    
    def get_day_theme(self, date: datetime) -> Dict[str, Any]:
        """Get theme for a specific date"""
        day_name = date.strftime("%A").lower()
        return self.themes.get(day_name, self.themes["monday"])
    
    def get_available_hero_images(self) -> List[str]:
        """Get list of available hero images for content generation"""
        if not self.hero_path.exists():
            return []
        
        images = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
            images.extend([f.name for f in self.hero_path.glob(ext)])
        return images
    
    def match_hero_to_theme(self, theme: Dict[str, Any], available_heroes: List[str]) -> Optional[str]:
        """Match a hero image to a theme based on filename keywords"""
        if not available_heroes:
            return None
        
        theme_keywords = []
        for outfit in theme.get("suggested_outfits", []):
            theme_keywords.extend(outfit.lower().split())
        for setting in theme.get("suggested_settings", []):
            theme_keywords.extend(setting.lower().split())
        
        for hero in available_heroes:
            hero_lower = hero.lower()
            for keyword in theme_keywords:
                if keyword in hero_lower:
                    return hero
        
        return available_heroes[0] if available_heroes else None
    
    async def generate_week_calendar(
        self,
        start_date: Optional[datetime] = None,
        posts_per_day: int = 2,
        use_ai_optimization: bool = True
    ) -> Dict[str, Any]:
        """Generate a week's content calendar with AI optimization"""
        
        if start_date is None:
            start_date = datetime.now()
            if start_date.weekday() != 0:
                start_date = start_date - timedelta(days=start_date.weekday())
        
        available_heroes = self.get_available_hero_images()
        calendar = {
            "influencer": self.influencer,
            "week_start": start_date.strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat(),
            "posts_per_day": posts_per_day,
            "total_posts": posts_per_day * 7,
            "days": []
        }
        
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            theme = self.get_day_theme(current_date)
            matched_hero = self.match_hero_to_theme(theme, available_heroes)
            
            day_schedule = {
                "date": current_date.strftime("%Y-%m-%d"),
                "day_name": current_date.strftime("%A"),
                "theme": theme["theme"],
                "vibe": theme["vibe"],
                "posts": []
            }
            
            for j in range(min(posts_per_day, len(theme["best_times"]))):
                post = {
                    "post_number": j + 1,
                    "scheduled_time": theme["best_times"][j],
                    "content_type": theme["content_type"],
                    "suggested_outfit": theme["suggested_outfits"][j % len(theme["suggested_outfits"])],
                    "suggested_setting": theme["suggested_settings"][j % len(theme["suggested_settings"])],
                    "hero_image": matched_hero,
                    "status": "planned",
                    "caption_prompt": None,
                    "cta_category": self._get_cta_category_for_theme(theme["theme"])
                }
                day_schedule["posts"].append(post)
            
            calendar["days"].append(day_schedule)
        
        if use_ai_optimization and self.xai_api_key:
            calendar = await self._optimize_calendar_with_ai(calendar)
        
        self._save_calendar(calendar)
        return calendar
    
    def _get_cta_category_for_theme(self, theme_name: str) -> str:
        """Map theme to optimal CTA category"""
        theme_cta_map = {
            "Motivation Monday": "soft_tease",
            "Tease Tuesday": "curiosity",
            "Wellness Wednesday": "soft_tease",
            "Thirsty Thursday": "direct",
            "Fanvue Friday": "exclusive",
            "Selfie Saturday": "soft_tease",
            "Soft Sunday": "curiosity"
        }
        return theme_cta_map.get(theme_name, "soft_tease")
    
    async def _optimize_calendar_with_ai(self, calendar: Dict[str, Any]) -> Dict[str, Any]:
        """Use Grok AI to generate caption prompts for each post"""
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                for day in calendar["days"]:
                    for post in day["posts"]:
                        prompt = f"""Generate a caption prompt for an AI influencer post.

Theme: {day['theme']}
Vibe: {day['vibe']}
Content Type: {post['content_type']}
Outfit: {post['suggested_outfit']}
Setting: {post['suggested_setting']}
Day: {day['day_name']}
Time: {post['scheduled_time']}

The influencer is Starbright Monroe - warm, direct, lightly flirty, engaging.
Target audience: Men ages 20-60.
Goal: Drive engagement and Fanvue subscriptions.

Generate a short, engaging caption (under 100 characters) that:
- Matches the theme and vibe
- Feels personal and direct
- Avoids influencer buzzwords
- Uses 1-2 relevant emojis max

Return ONLY the caption, nothing else."""

                        response = await client.post(
                            "https://api.x.ai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {self.xai_api_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": "grok-3-mini",
                                "messages": [{"role": "user", "content": prompt}],
                                "max_tokens": 100,
                                "temperature": 0.8
                            }
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            caption = result["choices"][0]["message"]["content"].strip()
                            caption = caption.strip('"\'')
                            post["caption_prompt"] = caption
                        
        except Exception as e:
            logger.error(f"AI optimization failed: {e}")
        
        return calendar
    
    def _save_calendar(self, calendar: Dict[str, Any]) -> str:
        """Save calendar to file"""
        week_start = calendar["week_start"]
        filename = f"calendar_{week_start}.json"
        filepath = self.calendar_path / filename
        
        with open(filepath, "w") as f:
            json.dump(calendar, f, indent=2)
        
        return str(filepath)
    
    def get_saved_calendars(self) -> List[Dict[str, Any]]:
        """Get list of saved calendars"""
        calendars = []
        for f in sorted(self.calendar_path.glob("calendar_*.json"), reverse=True):
            try:
                with open(f) as file:
                    cal = json.load(file)
                    calendars.append({
                        "filename": f.name,
                        "week_start": cal.get("week_start"),
                        "total_posts": cal.get("total_posts"),
                        "generated_at": cal.get("generated_at")
                    })
            except:
                pass
        return calendars
    
    def load_calendar(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load a specific calendar"""
        filepath = self.calendar_path / filename
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        return None
    
    def get_todays_posts(self) -> List[Dict[str, Any]]:
        """Get scheduled posts for today from the current calendar"""
        today = datetime.now().strftime("%Y-%m-%d")
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_start_str = week_start.strftime("%Y-%m-%d")
        
        calendar = self.load_calendar(f"calendar_{week_start_str}.json")
        if not calendar:
            return []
        
        for day in calendar.get("days", []):
            if day["date"] == today:
                return day["posts"]
        
        return []
    
    async def generate_month_calendar(
        self,
        year: int,
        month: int,
        posts_per_day: int = 2
    ) -> Dict[str, Any]:
        """Generate a full month's content calendar"""
        
        from calendar import monthrange
        
        first_day = datetime(year, month, 1)
        num_days = monthrange(year, month)[1]
        
        available_heroes = self.get_available_hero_images()
        calendar = {
            "influencer": self.influencer,
            "month": first_day.strftime("%B %Y"),
            "year": year,
            "month_number": month,
            "generated_at": datetime.now().isoformat(),
            "posts_per_day": posts_per_day,
            "total_posts": posts_per_day * num_days,
            "weeks": []
        }
        
        current_week = []
        for i in range(num_days):
            current_date = first_day + timedelta(days=i)
            theme = self.get_day_theme(current_date)
            matched_hero = self.match_hero_to_theme(theme, available_heroes)
            
            day_schedule = {
                "date": current_date.strftime("%Y-%m-%d"),
                "day_name": current_date.strftime("%A"),
                "theme": theme["theme"],
                "vibe": theme["vibe"],
                "posts": []
            }
            
            for j in range(min(posts_per_day, len(theme["best_times"]))):
                post = {
                    "post_number": j + 1,
                    "scheduled_time": theme["best_times"][j],
                    "content_type": theme["content_type"],
                    "suggested_outfit": theme["suggested_outfits"][j % len(theme["suggested_outfits"])],
                    "suggested_setting": theme["suggested_settings"][j % len(theme["suggested_settings"])],
                    "hero_image": matched_hero,
                    "status": "planned",
                    "cta_category": self._get_cta_category_for_theme(theme["theme"])
                }
                day_schedule["posts"].append(post)
            
            current_week.append(day_schedule)
            
            if current_date.weekday() == 6 or i == num_days - 1:
                calendar["weeks"].append(current_week)
                current_week = []
        
        month_filename = f"calendar_{year}_{month:02d}.json"
        filepath = self.calendar_path / month_filename
        with open(filepath, "w") as f:
            json.dump(calendar, f, indent=2)
        
        return calendar


_calendar_agents: Dict[str, ContentCalendarAgent] = {}


def get_calendar_agent(influencer: str = "starbright_monroe") -> ContentCalendarAgent:
    """Get or create a calendar agent for an influencer"""
    if influencer not in _calendar_agents:
        _calendar_agents[influencer] = ContentCalendarAgent(influencer)
    return _calendar_agents[influencer]
