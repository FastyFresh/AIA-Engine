"""
Stripe Client - Uses live Stripe API keys from secrets
"""
import os
import logging
import stripe

logger = logging.getLogger(__name__)
_stripe_settings = None

async def get_stripe_credentials():
    """Get Stripe credentials from environment secrets - always fetch fresh"""
    global _stripe_settings
    
    secret_key = os.environ.get("STRIPE_SECRET_KEY")
    publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY")
    
    if not secret_key or not publishable_key:
        raise ValueError("STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY must be set")
    
    key_type = "LIVE" if secret_key.startswith("sk_live") else "TEST"
    logger.info(f"Stripe initialized with {key_type} keys")
    
    _stripe_settings = {
        "publishable_key": publishable_key,
        "secret_key": secret_key
    }
    
    return _stripe_settings


def get_stripe_credentials_sync():
    """Synchronous version - get Stripe credentials - always fetch fresh"""
    secret_key = os.environ.get("STRIPE_SECRET_KEY")
    publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY")
    
    if not secret_key or not publishable_key:
        raise ValueError("STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY must be set")
    
    key_type = "LIVE" if secret_key.startswith("sk_live") else "TEST"
    logger.info(f"Stripe initialized with {key_type} keys")
    
    return {
        "publishable_key": publishable_key,
        "secret_key": secret_key
    }


async def get_stripe_client() -> stripe.StripeClient:
    """Get configured Stripe client"""
    credentials = await get_stripe_credentials()
    stripe.api_key = credentials["secret_key"]
    return stripe


def get_stripe_client_sync():
    """Synchronous version - Get configured Stripe client"""
    credentials = get_stripe_credentials_sync()
    stripe.api_key = credentials["secret_key"]
    return stripe
