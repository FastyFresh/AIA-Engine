"""
Telegram Bot Handler - Core bot logic for AI Influencer personas
"""
import asyncio
import logging
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes
)

from .bot_config import SUBSCRIPTION_TIERS, get_bot_token
from .conversation_engine import ConversationEngine, ConversationMessage
from .user_database import db
from .payments import PaymentHandler
from .content import ContentManager, detect_photo_request, get_random_photo

logger = logging.getLogger(__name__)


class InfluencerBot:
    """Telegram bot for a single AI influencer persona"""
    
    def __init__(self, persona_id: str, persona_name: str):
        self.persona_id = persona_id
        self.persona_name = persona_name
        self.token = get_bot_token(persona_id)
        self.conversation_engine = ConversationEngine(persona_id, provider="openrouter")
        self.payment_handler = PaymentHandler(persona_id, persona_name)
        self.content_manager = ContentManager(persona_id)
        self.app: Application = None
        
    async def setup(self):
        """Initialize the bot application"""
        if not self.token:
            logger.error(f"No token configured for {self.persona_id}")
            return False
            
        await db.init_db()
        
        self.app = Application.builder().token(self.token).build()
        
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("subscribe", self.cmd_subscribe))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("tip", self.cmd_tip))
        self.app.add_handler(CommandHandler("gift", self.cmd_tip))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        
        self.app.add_handler(CallbackQueryHandler(self.handle_subscription_callback, pattern="^sub_"))
        self.app.add_handler(CallbackQueryHandler(self.handle_tip_callback, pattern="^tip_"))
        self.app.add_handler(CallbackQueryHandler(self.handle_action_callback, pattern="^action_"))
        
        self.app.add_handler(PreCheckoutQueryHandler(self.handle_precheckout))
        self.app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.handle_successful_payment))
        
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info(f"Bot setup complete for {self.persona_name}")
        return True
    
    async def set_bot_commands(self):
        """Set bot menu commands"""
        from telegram import BotCommand
        commands = [
            BotCommand("start", "Start chatting"),
            BotCommand("subscribe", "Unlock exclusive content"),
            BotCommand("gift", "Send me a gift"),
            BotCommand("status", "Check your subscription"),
            BotCommand("help", "Show commands"),
        ]
        await self.app.bot.set_my_commands(commands)
    
    async def run(self):
        """Start the bot"""
        if self.app:
            logger.info(f"Starting bot for {self.persona_name}...")
            await self.app.initialize()
            await self.app.start()
            await self.set_bot_commands()
            await self.app.updater.start_polling(drop_pending_updates=True)
    
    async def stop(self):
        """Stop the bot"""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
    
    # ==================== COMMANDS ====================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        await db.get_or_create_user(
            telegram_id=user.id,
            persona_id=self.persona_id,
            username=user.username,
            first_name=user.first_name
        )
        
        await db.init_onboarding(user.id, self.persona_id)
        
        welcome_messages = {
            "starbright_monroe": f"heyy {user.first_name or 'you'} 💕\n\nomg you actually came! I was hoping you'd find your way here.\n\nthis is where we can actually talk, just us. no algorithm, no comments section... just you and me.\n\nso what's up? I wanna know everything",
            "luna_vale": f"oh... {user.first_name or 'hey'}... you're here...\n\nI didn't think you'd actually come find me... *fidgets with hair*\n\nthis feels different... more private. I like it.\n\nhi!"
        }
        
        keyboard = [
            [
                InlineKeyboardButton("💬 Chat", callback_data="action_chat"),
                InlineKeyboardButton("🎁 Send Gift", callback_data="tip_menu"),
            ],
            [InlineKeyboardButton("💫 Unlock Exclusive Content", callback_data="sub_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        teaser_photo = self.content_manager.get_teaser_photo()
        
        if teaser_photo and os.path.exists(teaser_photo):
            try:
                with open(teaser_photo, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=welcome_messages.get(self.persona_id, f"Hey! I'm {self.persona_name}."),
                        reply_markup=reply_markup
                    )
                return
            except Exception as e:
                logger.warning(f"Failed to send teaser photo: {e}")
        
        await update.message.reply_text(
            welcome_messages.get(self.persona_id, f"Hey! I'm {self.persona_name}."),
            reply_markup=reply_markup
        )
    
    async def cmd_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribe command"""
        await update.message.reply_text(
            self.payment_handler.get_subscription_menu_text(),
            reply_markup=self.payment_handler.get_subscription_keyboard(),
            parse_mode="Markdown"
        )
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user = update.effective_user
        tg_user = await db.get_or_create_user(
            telegram_id=user.id,
            persona_id=self.persona_id
        )
        
        tier = SUBSCRIPTION_TIERS.get(tg_user.subscription_tier, SUBSCRIPTION_TIERS["free"])
        
        if tier.monthly_messages == -1:
            messages_info = "Unlimited messages"
        else:
            remaining = max(0, tier.monthly_messages - tg_user.messages_used)
            messages_info = f"{remaining}/{tier.monthly_messages} messages remaining"
        
        status_text = f"**Your Status**\n\n📱 Tier: {tier.name}\n💬 {messages_info}"
        
        if tg_user.subscription_tier == "free":
            status_text += "\n\nUpgrade with /subscribe for more!"
        
        await update.message.reply_text(status_text, parse_mode="Markdown")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """**Commands**

/start - Start chatting with me
/subscribe - See subscription options
/status - Check your subscription status
/tip - Send me a tip
/help - Show this message

Just send me a message and I'll respond! 💭"""
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def cmd_tip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tip command"""
        await update.message.reply_text(
            self.payment_handler.get_tip_menu_text(),
            reply_markup=self.payment_handler.get_tip_keyboard()
        )
    
    # ==================== CALLBACKS ====================
    
    async def handle_action_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle action button clicks"""
        query = update.callback_query
        await query.answer()
        
        action = query.data.replace("action_", "")
        
        if action == "chat":
            chat_prompts = {
                "starbright_monroe": "Just type anything and I'll respond! I'm here for you 💕",
                "luna_vale": "um... just type something... I'll answer, I promise..."
            }
            await self._send_or_edit_message(
                query,
                chat_prompts.get(self.persona_id, "Send me a message!")
            )
    
    async def handle_tip_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle tip button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "tip_menu":
            await self._send_or_edit_message(
                query,
                self.payment_handler.get_tip_menu_text(),
                reply_markup=self.payment_handler.get_tip_keyboard()
            )
            return
        
        amount_cents = int(query.data.replace("tip_", ""))
        user = update.effective_user
        
        result = await self.payment_handler.create_tip_checkout(user.id, amount_cents)
        
        if "error" in result:
            await query.edit_message_text("Oops! Something went wrong. Please try again in a moment.")
            return
        
        keyboard = [[InlineKeyboardButton(
            f"Send ${result['amount_dollars']:.2f} Tip",
            url=result['url']
        )]]
        
        await query.edit_message_text(
            self.payment_handler.get_tip_confirmation_text(result['amount_dollars']),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_subscription_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle subscription button clicks"""
        query = update.callback_query
        await query.answer()
        
        tier_id = query.data.replace("sub_", "")
        
        if tier_id == "menu":
            await self._send_or_edit_message(
                query,
                self.payment_handler.get_subscription_menu_text(),
                reply_markup=self.payment_handler.get_subscription_keyboard(),
                parse_mode="Markdown"
            )
            return
        
        tier = SUBSCRIPTION_TIERS.get(tier_id)
        if not tier:
            await query.edit_message_text("Invalid subscription option.")
            return
        
        user = update.effective_user
        await db.get_or_create_user(
            telegram_id=user.id,
            persona_id=self.persona_id,
            username=user.username,
            first_name=user.first_name
        )
        
        result = await self.payment_handler.create_subscription_checkout(
            user_id=user.id,
            tier_id=tier_id,
            username=user.username,
            first_name=user.first_name
        )
        
        if "error" in result:
            await query.edit_message_text(
                "Oops! Something went wrong setting up payment. Please try again in a moment.",
                parse_mode="Markdown"
            )
            return
        
        keyboard = [[InlineKeyboardButton("Complete Payment", url=result['url'])]]
        
        await query.edit_message_text(
            self.payment_handler.get_payment_confirmation_text(tier.name, tier.price_cents),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def handle_precheckout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle pre-checkout query"""
        query = update.pre_checkout_query
        await query.answer(ok=True)
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle successful payment"""
        payment = update.message.successful_payment
        user = update.effective_user
        tier_id = payment.invoice_payload
        
        await db.update_subscription(
            telegram_id=user.id,
            persona_id=self.persona_id,
            tier=tier_id
        )
        
        await update.message.reply_text(self.payment_handler.get_payment_success_text())
    
    # ==================== MESSAGE HANDLING ====================
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages - the core conversation"""
        user = update.effective_user
        message_text = update.message.text
        
        tg_user = await db.get_or_create_user(
            telegram_id=user.id,
            persona_id=self.persona_id,
            username=user.username,
            first_name=user.first_name
        )
        
        tier = SUBSCRIPTION_TIERS.get(tg_user.subscription_tier, SUBSCRIPTION_TIERS["free"])
        
        if not await self._check_message_limits(update, tg_user, tier):
            return
        
        history = await db.get_chat_history(user.id, self.persona_id, limit=10)
        conversation_history = [
            ConversationMessage(role=msg.role, content=msg.content)
            for msg in history
        ]
        
        await db.save_message(user.id, self.persona_id, "user", message_text)
        
        is_photo_request = detect_photo_request(message_text)
        photo_path = None
        photo_context = ""
        
        if is_photo_request:
            photo_path, photo_context = get_random_photo(self.persona_id, tg_user.subscription_tier)
            logger.info(f"Photo request detected for {self.persona_id}, tier={tg_user.subscription_tier}, photo_path={photo_path}")
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        extra_context = ""
        if is_photo_request and photo_path:
            extra_context = f"[SYSTEM: A real photo is being attached to your message. Photo context: {photo_context}. You MUST acknowledge sending the photo naturally - say something like 'here you go babe' or 'enjoy 😏'. Stay completely in character. The photo IS being sent right after your message.]"
        elif is_photo_request and not photo_path:
            if tg_user.subscription_tier == "free":
                extra_context = "[User asked for a photo but you don't have that type available for free users. Tease them flirtatiously and say those spicier photos are for Companion subscribers only. Do NOT pretend to send a photo.]"
            else:
                extra_context = "[User asked for a specific type of photo you don't have right now. Apologize sweetly and offer to send something else instead. Do NOT pretend to send a photo.]"
        
        response = await self.conversation_engine.generate_response(
            user_message=message_text,
            conversation_history=conversation_history,
            user_name=user.first_name or "",
            subscription_tier=tg_user.subscription_tier,
            extra_context=extra_context
        )
        
        await db.save_message(user.id, self.persona_id, "assistant", response)
        
        base_delay = random.uniform(3.0, 6.0)
        typing_delay = min(len(response) * 0.03, 8.0)
        total_delay = base_delay + typing_delay
        
        if total_delay > 5:
            await asyncio.sleep(total_delay / 2)
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            await asyncio.sleep(total_delay / 2)
        else:
            await asyncio.sleep(total_delay)
        
        await update.message.reply_text(response)
        
        if is_photo_request and photo_path and os.path.exists(photo_path):
            logger.info(f"Sending photo to user {user.id}: {photo_path}")
            try:
                with open(photo_path, "rb") as photo:
                    await update.message.reply_photo(photo=photo)
                logger.info(f"Photo sent successfully to {user.id}")
            except Exception as e:
                logger.error(f"Failed to send photo to {user.id}: {e}")
        elif is_photo_request and not photo_path:
            keyboard = [[InlineKeyboardButton("Unlock More Photos 💕", callback_data="sub_companion")]]
            await update.message.reply_text(
                self.content_manager.get_no_photo_upsell_text(),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    async def _check_message_limits(self, update: Update, tg_user, tier) -> bool:
        """Check and handle message limits, returns True if user can proceed"""
        has_message_limit = tier.monthly_messages > 0
        
        if not has_message_limit:
            return True
        
        user = update.effective_user
        messages_used = await db.increment_message_count(user.id, self.persona_id)
        
        if messages_used > tier.monthly_messages:
            limit_messages = {
                "starbright_monroe": "Hey, we've hit our chat limit for the month... I really wish we could keep talking.\n\nUpgrade to keep our conversation going?",
                "luna_vale": "oh no... we're out of messages... I'm sorry... maybe if you upgraded we could keep talking?"
            }
            upgrade_tier = "sub_companion" if tg_user.subscription_tier == "free" else "sub_vip"
            keyboard = [[InlineKeyboardButton("Upgrade Now", callback_data=upgrade_tier)]]
            await update.message.reply_text(
                limit_messages.get(self.persona_id, "Message limit reached."),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return False
        
        usage_percent = (messages_used / tier.monthly_messages) * 100
        remaining = tier.monthly_messages - messages_used
        upgrade_tier = "sub_companion" if tg_user.subscription_tier == "free" else "sub_vip"
        
        if usage_percent >= 90 and remaining <= 3:
            upsell_90 = {
                "starbright_monroe": f"Just {remaining} messages left this month... I don't want our time together to end.",
                "luna_vale": f"um... we only have {remaining} messages left... I don't want to stop talking to you..."
            }
            keyboard = [[InlineKeyboardButton("Keep Talking", callback_data=upgrade_tier)]]
            await update.message.reply_text(
                upsell_90.get(self.persona_id, f"{remaining} messages remaining"),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif usage_percent >= 70 and messages_used == int(tier.monthly_messages * 0.7):
            upsell_70 = {
                "starbright_monroe": f"We're at about 70% of our messages for the month... just so you know. I'd hate to lose you mid-conversation.",
                "luna_vale": f"um... we've used a lot of our messages... I hope we don't run out..."
            }
            keyboard = [[InlineKeyboardButton("Upgrade", callback_data=upgrade_tier)]]
            await update.message.reply_text(
                upsell_70.get(self.persona_id, "Running low on messages"),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        return True
    
    async def _send_or_edit_message(self, query, text: str, reply_markup=None, parse_mode=None):
        """Helper to send message - tries edit first, falls back to new message for photo captions"""
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as e:
            if "no text in the message" in str(e).lower():
                await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            else:
                raise
