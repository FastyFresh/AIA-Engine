"""
Run both AI Influencer Telegram Bots
"""
import asyncio
import logging
import signal
import sys

from .bot_handler import InfluencerBot
from .user_database import db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

PERSONAS = [
    ("starbright_monroe", "Starbright Monroe"),
    ("luna_vale", "Luna Vale")
]

async def send_reengagement_nudges(bots: list):
    """Background task to send 'hi' to users inactive for 24+ hours"""
    while True:
        try:
            await asyncio.sleep(3600)
            
            for bot in bots:
                try:
                    inactive_users = await db.get_inactive_users(bot.persona_id, hours=24)
                    
                    for user in inactive_users:
                        try:
                            await bot.application.bot.send_message(
                                chat_id=user['telegram_id'],
                                text="hi 💕"
                            )
                            await db.mark_user_nudged(user['telegram_id'], bot.persona_id)
                            logger.info(f"Sent nudge to user {user['telegram_id']} for {bot.persona_id}")
                            await asyncio.sleep(1)
                        except Exception as e:
                            logger.warning(f"Failed to nudge user {user['telegram_id']}: {e}")
                            
                except Exception as e:
                    logger.error(f"Error in nudge task for {bot.persona_id}: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Nudge task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in reengagement task: {e}")
            await asyncio.sleep(60)

async def run_all_bots():
    """Run all persona bots concurrently"""
    bots = []
    
    for persona_id, persona_name in PERSONAS:
        bot = InfluencerBot(persona_id, persona_name)
        if await bot.setup():
            bots.append(bot)
        else:
            logger.warning(f"Skipping {persona_name} - no token configured")
    
    if not bots:
        logger.error("No bots configured! Add TELEGRAM_BOT_TOKEN_* environment variables.")
        return
    
    logger.info(f"Starting {len(bots)} bots...")
    
    for bot in bots:
        await bot.run()
    
    logger.info("All bots are running! Press Ctrl+C to stop.")
    
    nudge_task = asyncio.create_task(send_reengagement_nudges(bots))
    logger.info("Re-engagement nudge task started (checks hourly)")
    
    stop_event = asyncio.Event()
    
    def signal_handler():
        logger.info("Shutting down bots...")
        stop_event.set()
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    await stop_event.wait()
    
    nudge_task.cancel()
    try:
        await nudge_task
    except asyncio.CancelledError:
        pass
    
    for bot in bots:
        await bot.stop()
    
    logger.info("All bots stopped.")

def main():
    """Entry point for running bots"""
    asyncio.run(run_all_bots())

if __name__ == "__main__":
    main()
