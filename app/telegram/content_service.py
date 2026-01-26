"""
Content Delivery Service for Telegram Bots
Handles drip onboarding, content drops, and teaser generation
"""
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from .user_database import db
from .bot_config import get_bot_token

logger = logging.getLogger(__name__)

CONTENT_DIR = Path("content/final")
TEASER_DIR = Path("content/teasers")
TELEGRAM_CONTENT_DIR = Path("content/telegram")

WELCOME_PACK_CONFIG = {
    "starbright_monroe": {
        "companion": {
            "message": """Welcome to the inner circle! I'm so happy you're here.

Here's a little something to get us started... just for you.

I'll be sending exclusive photos and moments that I don't share anywhere else. This is where the real me lives.

Can't wait to get to know you better.""",
            "content_count": 3,
            "folder": "companion"
        },
        "vip": {
            "message": """VIP access unlocked. You really went all in, didn't you?

I love that about you.

Here's your first exclusive drop - the stuff I save for my closest people. Custom requests are open now too, so don't be shy.

This is going to be fun.""",
            "content_count": 5,
            "folder": "vip"
        }
    },
    "luna_vale": {
        "companion": {
            "message": """You're in.

Not everyone gets this far. Here's a taste of what you've been missing.

More coming soon. Stay ready.""",
            "content_count": 3,
            "folder": "companion"
        },
        "vip": {
            "message": """VIP. Bold choice.

You wanted the real Luna? Here she is. No filters, no limits.

Custom requests are open. Show me what you've got.""",
            "content_count": 5,
            "folder": "vip"
        }
    }
}

ONBOARDING_MESSAGES = {
    "starbright_monroe": {
        0: """Hey! Just wanted to say... I'm really glad you're here.

I share exclusive photos and moments with my subscribers - things I don't post anywhere else. Cozy mornings, golden hour shoots, the real behind-the-scenes stuff.

If that sounds like something you'd enjoy, check out /subscribe

No pressure though. I'm just happy to chat.""",
        3: """Been thinking about you...

My Companion subscribers just got some new photos from my weekend shoot. Wish I could show you.

Want to join them? /subscribe""",
        7: """It's been a week since we met! Time flies.

Just sent out exclusive content to my subscribers - they're loving it.

This is your last nudge from me. If you want to get closer, /subscribe is there for you.

Either way, I'm here when you want to talk."""
    },
    "luna_vale": {
        0: """So you found me.

I share things here I don't share anywhere else. Late night looks, underground fashion, the stuff that's too real for the main feed.

If you think you can handle it, /subscribe

Or don't. Your choice.""",
        3: """Still here? Interesting.

Just dropped some exclusive content for my subscribers. The aesthetic is immaculate.

/subscribe if you want in.""",
        7: """Week one, done.

My VIPs and Companions get the real Luna experience. Custom content, priority access, no limits.

Last time I'm bringing it up. /subscribe or don't. But you know you're curious."""
    }
}


class ContentService:
    """Handles content delivery to subscribers"""
    
    def __init__(self, persona_id: str):
        self.persona_id = persona_id
        self.token = get_bot_token(persona_id)
        self.bot = Bot(token=self.token) if self.token else None
    
    async def send_onboarding_messages(self, day: int) -> int:
        """Send onboarding messages for a specific day to eligible users"""
        if not self.bot:
            return 0
        
        users = await db.get_users_for_onboarding(self.persona_id, day)
        message = ONBOARDING_MESSAGES.get(self.persona_id, {}).get(day, "")
        
        if not message:
            return 0
        
        sent_count = 0
        for user in users:
            try:
                keyboard = [[InlineKeyboardButton("View Options", callback_data="sub_companion")]]
                await self.bot.send_message(
                    chat_id=user["telegram_id"],
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                await db.mark_onboarding_sent(user["telegram_id"], self.persona_id, day)
                sent_count += 1
                logger.info(f"Sent day {day} onboarding to user {user['telegram_id']}")
            except Exception as e:
                logger.error(f"Failed to send onboarding to {user['telegram_id']}: {e}")
        
        return sent_count
    
    async def send_content_drop(
        self,
        content_path: str,
        caption: str,
        tier: str = "companion",
        content_type: str = "photo"
    ) -> int:
        """Send exclusive content to all subscribers of a tier"""
        if not self.bot:
            return 0
        
        subscribers = await db.get_subscribers_for_content(self.persona_id, tier)
        
        sent_count = 0
        for sub in subscribers:
            try:
                if content_type == "photo":
                    with open(content_path, "rb") as photo:
                        await self.bot.send_photo(
                            chat_id=sub["telegram_id"],
                            photo=photo,
                            caption=caption
                        )
                elif content_type == "video":
                    with open(content_path, "rb") as video:
                        await self.bot.send_video(
                            chat_id=sub["telegram_id"],
                            video=video,
                            caption=caption
                        )
                
                await db.record_content_drop(
                    sub["telegram_id"],
                    self.persona_id,
                    content_type,
                    content_path,
                    tier
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send content to {sub['telegram_id']}: {e}")
        
        return sent_count
    
    async def send_teaser_to_free_users(self, teaser_path: str, caption: str) -> int:
        """Send watermarked teaser content to free users"""
        if not self.bot:
            return 0
        
        from .user_database import aiosqlite
        
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT telegram_id, first_name
                FROM users
                WHERE persona_id = ? AND subscription_tier = 'free'
            """, (self.persona_id,))
            users = await cursor.fetchall()
        
        teaser_captions = {
            "starbright_monroe": f"{caption}\n\n[Preview only - /subscribe for the full gallery]",
            "luna_vale": f"{caption}\n\n[Teaser - unlock the full set with /subscribe]"
        }
        
        sent_count = 0
        for user in users:
            try:
                with open(teaser_path, "rb") as photo:
                    await self.bot.send_photo(
                        chat_id=user["telegram_id"],
                        photo=photo,
                        caption=teaser_captions.get(self.persona_id, caption)
                    )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send teaser to {user['telegram_id']}: {e}")
        
        return sent_count
    
    async def send_churn_winback(self, telegram_id: int, first_name: str = "") -> bool:
        """Send a win-back message when user cancels subscription"""
        if not self.bot:
            return False
        
        winback_messages = {
            "starbright_monroe": f"""Hey{' ' + first_name if first_name else ''}...

I noticed you left. I won't pretend that doesn't sting a little.

If something wasn't right, I'd love to know. And if you ever want to come back, I'll be here.

Miss you already.""",
            "luna_vale": f"""So you're leaving{', ' + first_name if first_name else ''}.

Didn't think you'd be the type to bail. But whatever.

Door's always open if you change your mind. /subscribe

No hard feelings. Mostly."""
        }
        
        try:
            keyboard = [[InlineKeyboardButton("Come Back", callback_data="sub_companion")]]
            await self.bot.send_message(
                chat_id=telegram_id,
                text=winback_messages.get(self.persona_id, "We miss you!"),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send winback to {telegram_id}: {e}")
            return False

    async def send_welcome_pack(
        self,
        telegram_id: int,
        tier: str,
        first_name: str = ""
    ) -> int:
        """Send welcome pack content to a new subscriber"""
        if not self.bot:
            logger.error("Bot not initialized for welcome pack")
            return 0
        
        config = WELCOME_PACK_CONFIG.get(self.persona_id, {}).get(tier)
        if not config:
            logger.warning(f"No welcome pack config for {self.persona_id}/{tier}")
            return 0
        
        persona_short = "starbright" if self.persona_id == "starbright_monroe" else "luna"
        content_folder = TELEGRAM_CONTENT_DIR / persona_short / config["folder"]
        
        if not content_folder.exists():
            logger.warning(f"Welcome pack folder not found: {content_folder}")
            return 0
        
        image_files = [
            f for f in content_folder.iterdir()
            if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
        ]
        image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        files_to_send = image_files[:config["content_count"]]
        
        if not files_to_send:
            logger.warning(f"No images found in {content_folder}")
            return 0
        
        try:
            welcome_msg = config["message"]
            if first_name:
                welcome_msg = f"Hey {first_name}!\n\n" + welcome_msg
            await self.bot.send_message(chat_id=telegram_id, text=welcome_msg)
            
            sent_count = 0
            for i, file_path in enumerate(files_to_send):
                try:
                    caption = f"[{i+1}/{len(files_to_send)}]" if len(files_to_send) > 1 else None
                    with open(file_path, "rb") as photo:
                        await self.bot.send_photo(
                            chat_id=telegram_id,
                            photo=photo,
                            caption=caption
                        )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send welcome photo {file_path}: {e}")
            
            logger.info(f"Sent {sent_count} welcome pack images to {telegram_id} for {tier}")
            return sent_count
            
        except Exception as e:
            logger.error(f"Failed to send welcome pack to {telegram_id}: {e}")
            return 0


async def run_onboarding_jobs():
    """Run all onboarding message jobs - call this from a scheduler"""
    for persona_id in ["starbright_monroe", "luna_vale"]:
        service = ContentService(persona_id)
        for day in [0, 3, 7]:
            count = await service.send_onboarding_messages(day)
            if count > 0:
                logger.info(f"Sent day {day} onboarding to {count} users for {persona_id}")
