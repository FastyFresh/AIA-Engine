"""Payment and Stripe webhook routes"""
import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["payments"])


@router.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events for payment completion"""
    try:
        from app.services.stripe_client import get_stripe_client
        from app.telegram.user_database import db as telegram_db
        
        stripe = await get_stripe_client()
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        event_data = json.loads(payload)
        event_type = event_data.get("type", "")
        
        logger.info(f"Received Stripe webhook: {event_type}")
        
        if event_type == "checkout.session.completed":
            session = event_data["data"]["object"]
            metadata = session.get("metadata", {})
            
            telegram_user_id = metadata.get("telegram_user_id")
            persona_id = metadata.get("persona_id")
            tier_id = metadata.get("tier_id")
            
            if telegram_user_id and persona_id and tier_id:
                await telegram_db.init_db()
                await telegram_db.update_subscription(
                    telegram_id=int(telegram_user_id),
                    persona_id=persona_id,
                    tier=tier_id
                )
                logger.info(f"Updated subscription for user {telegram_user_id}: {tier_id}")
                
                try:
                    from app.telegram.content_service import ContentService
                    content_service = ContentService(persona_id)
                    user = await telegram_db.get_or_create_user(
                        telegram_id=int(telegram_user_id),
                        persona_id=persona_id
                    )
                    first_name = user.first_name if user and user.first_name else ""
                    welcome_count = await content_service.send_welcome_pack(
                        telegram_id=int(telegram_user_id),
                        tier=tier_id,
                        first_name=first_name
                    )
                    logger.info(f"Sent {welcome_count} welcome pack images to user {telegram_user_id}")
                except Exception as e:
                    logger.error(f"Failed to send welcome pack: {e}")
        
        elif event_type == "customer.subscription.deleted":
            subscription = event_data["data"]["object"]
            metadata = subscription.get("metadata", {})
            telegram_user_id = metadata.get("telegram_user_id")
            persona_id = metadata.get("persona_id")
            
            if telegram_user_id and persona_id:
                await telegram_db.init_db()
                
                user = await telegram_db.get_or_create_user(
                    telegram_id=int(telegram_user_id),
                    persona_id=persona_id
                )
                
                await telegram_db.update_subscription(
                    telegram_id=int(telegram_user_id),
                    persona_id=persona_id,
                    tier="free"
                )
                logger.info(f"Cancelled subscription for user {telegram_user_id}")
                
                try:
                    from app.telegram.content_service import ContentService
                    content_service = ContentService(persona_id)
                    await content_service.send_churn_winback(
                        int(telegram_user_id),
                        user.first_name or ""
                    )
                    logger.info(f"Sent win-back message to {telegram_user_id}")
                except Exception as winback_error:
                    logger.error(f"Failed to send win-back: {winback_error}")
        
        return {"received": True}
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return JSONResponse(status_code=400, content={"error": str(e)})


@router.get("/payment/success")
async def payment_success(session_id: str = None):
    """Payment success page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Successful</title>
        <style>
            body { font-family: -apple-system, system-ui, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
            .container { background: white; padding: 40px; border-radius: 16px; max-width: 400px; margin: 0 auto; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
            h1 { color: #10b981; }
            p { color: #666; margin: 20px 0; }
            .emoji { font-size: 64px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="emoji">✨</div>
            <h1>Payment Successful!</h1>
            <p>Thank you for subscribing! Your subscription is now active.</p>
            <p>Go back to Telegram to continue your conversation.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/payment/cancel")
async def payment_cancel():
    """Payment cancelled page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Cancelled</title>
        <style>
            body { font-family: -apple-system, system-ui, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
            .container { background: white; padding: 40px; border-radius: 16px; max-width: 400px; margin: 0 auto; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
            h1 { color: #f59e0b; }
            p { color: #666; margin: 20px 0; }
            .emoji { font-size: 64px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="emoji">😔</div>
            <h1>Payment Cancelled</h1>
            <p>No worries! You can try again anytime.</p>
            <p>Go back to Telegram if you change your mind.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
