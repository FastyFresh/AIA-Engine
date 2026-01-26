"""
Telegram Payments Module - Stripe checkout and payment handling
"""
import os
import logging
from typing import Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .bot_config import SUBSCRIPTION_TIERS, get_stripe_price_id
from ..services.stripe_client import get_stripe_client

logger = logging.getLogger(__name__)


class PaymentHandler:
    """Handles all Stripe payment operations for a persona"""
    
    def __init__(self, persona_id: str, persona_name: str):
        self.persona_id = persona_id
        self.persona_name = persona_name
    
    def _get_base_url(self) -> str:
        """Get the base URL for payment redirects"""
        domains = os.environ.get("REPLIT_DOMAINS", "").split(",")
        return f"https://{domains[0]}" if domains else "https://example.com"
    
    async def create_subscription_checkout(
        self, 
        user_id: int, 
        tier_id: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> dict:
        """Create a Stripe checkout session for subscription"""
        tier = SUBSCRIPTION_TIERS.get(tier_id)
        if not tier:
            return {"error": "Invalid subscription tier"}
        
        stripe_price_id = get_stripe_price_id(self.persona_id, tier_id)
        if not stripe_price_id:
            return {"error": "Tier not available for purchase"}
        
        try:
            stripe = await get_stripe_client()
            base_url = self._get_base_url()
            
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price": stripe_price_id,
                    "quantity": 1
                }],
                mode="subscription",
                success_url=f"{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{base_url}/payment/cancel",
                client_reference_id=f"{user_id}:{self.persona_id}:{tier_id}",
                metadata={
                    "telegram_user_id": str(user_id),
                    "persona_id": self.persona_id,
                    "tier_id": tier_id
                }
            )
            
            return {
                "success": True,
                "url": session.url,
                "tier": tier
            }
            
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            return {"error": str(e)}
    
    async def create_tip_checkout(self, user_id: int, amount_cents: int) -> dict:
        """Create a Stripe checkout session for a one-time tip"""
        amount_dollars = amount_cents / 100
        
        try:
            stripe = await get_stripe_client()
            base_url = self._get_base_url()
            
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": f"Tip for {self.persona_name}",
                            "description": f"One-time tip of ${amount_dollars:.2f}"
                        }
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=f"{base_url}/payment/success?type=tip",
                cancel_url=f"{base_url}/payment/cancel",
                metadata={
                    "telegram_user_id": str(user_id),
                    "persona_id": self.persona_id,
                    "type": "tip",
                    "amount": str(amount_cents)
                }
            )
            
            return {
                "success": True,
                "url": session.url,
                "amount_dollars": amount_dollars
            }
            
        except Exception as e:
            logger.error(f"Failed to create tip checkout session: {e}")
            return {"error": str(e)}
    
    def get_subscription_menu_text(self) -> str:
        """Get persona-specific subscription menu text"""
        tier_info = {
            "starbright_monroe": "Want to get closer? Here's what I can offer:\n\n💫 **Companion** ($9.99/mo)\n• 500 messages per month\n• Exclusive photos just for you\n• I'll remember our conversations\n\n👑 **VIP** ($24.99/mo)\n• Unlimited messages\n• Custom photo requests\n• Video content\n• Our own little world",
            "luna_vale": "So you want more of me? Interesting.\n\n💫 **Companion** ($9.99/mo)\n• 500 messages\n• Exclusive content\n• I might actually remember you\n\n👑 **VIP** ($24.99/mo)\n• Unlimited access\n• Custom requests\n• Video content\n• The real Luna experience"
        }
        return tier_info.get(self.persona_id, "Choose your subscription:")
    
    def get_tip_menu_text(self) -> str:
        """Get persona-specific tip menu text"""
        tip_messages = {
            "starbright_monroe": "Aww, you want to send me a gift? That's so sweet! 💕 Pick an amount:",
            "luna_vale": "Feeling generous? I like that energy. Choose your amount:"
        }
        return tip_messages.get(self.persona_id, "Pick an amount:")
    
    def get_payment_confirmation_text(self, tier_name: str, price_cents: int) -> str:
        """Get persona-specific payment confirmation text"""
        payment_messages = {
            "starbright_monroe": f"Ready to join me? Click below to complete your **{tier_name}** subscription (${price_cents/100:.2f}/month).\n\nI can't wait to get closer with you! 💕",
            "luna_vale": f"So you're serious. **{tier_name}** - ${price_cents/100:.2f}/month.\n\nClick below if you can handle it."
        }
        return payment_messages.get(self.persona_id, f"Complete your {tier_name} subscription:")
    
    def get_tip_confirmation_text(self, amount_dollars: float) -> str:
        """Get persona-specific tip confirmation text"""
        tip_confirm_messages = {
            "starbright_monroe": f"You're amazing! Click below to send your ${amount_dollars:.2f} tip 💕",
            "luna_vale": f"${amount_dollars:.2f}? Bold. I respect it. Click to complete:"
        }
        return tip_confirm_messages.get(self.persona_id, f"Click to send ${amount_dollars:.2f} tip:")
    
    def get_payment_success_text(self) -> str:
        """Get persona-specific payment success text"""
        success_messages = {
            "starbright_monroe": "Thank you so much! 💕 This means a lot to me. Can't wait to share more with you.",
            "luna_vale": "Well, well. You're serious. I like that. Let's see what trouble we can get into."
        }
        return success_messages.get(self.persona_id, "Thank you for subscribing!")
    
    @staticmethod
    def get_subscription_keyboard():
        """Get standard subscription options keyboard"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💫 Companion - $9.99/mo", callback_data="sub_companion")],
            [InlineKeyboardButton("👑 VIP - $24.99/mo", callback_data="sub_vip")]
        ])
    
    @staticmethod
    def get_tip_keyboard():
        """Get standard tip options keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("$5 ☕", callback_data="tip_500"),
                InlineKeyboardButton("$10 💐", callback_data="tip_1000"),
            ],
            [
                InlineKeyboardButton("$25 💝", callback_data="tip_2500"),
                InlineKeyboardButton("$50 🔥", callback_data="tip_5000"),
            ]
        ])
