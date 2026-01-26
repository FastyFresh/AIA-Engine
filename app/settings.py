"""
Centralized Settings - Single source of truth for all configuration

Uses Pydantic for type validation and environment variable loading.
All services should import from here instead of calling os.getenv directly.

SECURITY NOTES:
- Never log secret values or their prefixes
- Use SecretStr for sensitive values
- All secrets loaded from environment at startup
"""

import os
import logging
from typing import Optional
from functools import lru_cache
from pydantic import BaseModel, Field, SecretStr

logger = logging.getLogger(__name__)


class APISettings(BaseModel):
    """External API credentials - all sensitive values"""
    
    fal_key: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("FAL_KEY", "")))
    replicate_api_token: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("REPLICATE_API_TOKEN", "")))
    xai_api_key: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("XAI_API_KEY", "")))
    openrouter_api_key: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("OPENROUTER_API_KEY", "")))
    apify_api_token: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("APIFY_API_TOKEN", "")))
    
    admin_api_key: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("ADMIN_API_KEY", "")))
    
    @property
    def fal_configured(self) -> bool:
        return bool(self.fal_key.get_secret_value())
    
    @property
    def replicate_configured(self) -> bool:
        return bool(self.replicate_api_token.get_secret_value())
    
    @property
    def xai_configured(self) -> bool:
        return bool(self.xai_api_key.get_secret_value())
    
    @property
    def openrouter_configured(self) -> bool:
        return bool(self.openrouter_api_key.get_secret_value())


class StripeSettings(BaseModel):
    """Stripe payment configuration"""
    
    secret_key: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("STRIPE_SECRET_KEY", "")))
    publishable_key: str = Field(default_factory=lambda: os.getenv("STRIPE_PUBLISHABLE_KEY", ""))
    webhook_secret: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("STRIPE_WEBHOOK_SECRET", "")))
    
    @property
    def is_live(self) -> bool:
        key = self.secret_key.get_secret_value()
        return key.startswith("sk_live_") if key else False
    
    @property
    def is_configured(self) -> bool:
        return bool(self.secret_key.get_secret_value() and self.publishable_key)
    
    def log_status(self):
        """Log Stripe configuration status without exposing keys"""
        if self.is_configured:
            mode = "LIVE" if self.is_live else "TEST"
            logger.info(f"Stripe initialized with {mode} keys")
        else:
            logger.warning("Stripe not configured - missing keys")


class TwitterSettings(BaseModel):
    """Twitter/X API configuration"""
    
    client_id: str = Field(default_factory=lambda: os.getenv("TWITTER_CLIENT_ID", ""))
    client_secret: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("TWITTER_CLIENT_SECRET", "")))
    api_key: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("TWITTER_API_KEY", "")))
    api_secret: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("TWITTER_API_SECRET", "")))
    access_token: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("TWITTER_ACCESS_TOKEN", "")))
    access_token_secret: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")))
    
    @property
    def oauth2_configured(self) -> bool:
        return bool(self.client_id and self.client_secret.get_secret_value())
    
    @property
    def oauth1_configured(self) -> bool:
        return bool(
            self.api_key.get_secret_value() and 
            self.api_secret.get_secret_value() and
            self.access_token.get_secret_value() and
            self.access_token_secret.get_secret_value()
        )


class TelegramSettings(BaseModel):
    """Telegram bot configuration"""
    
    bot_token_starbright: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("TELEGRAM_BOT_TOKEN_STARBRIGHT", "")))
    bot_token_luna: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("TELEGRAM_BOT_TOKEN_LUNA", "")))
    
    def get_token(self, persona_id: str) -> str:
        """Get bot token for a persona"""
        if "starbright" in persona_id.lower():
            return self.bot_token_starbright.get_secret_value()
        elif "luna" in persona_id.lower():
            return self.bot_token_luna.get_secret_value()
        return ""
    
    @property
    def starbright_configured(self) -> bool:
        return bool(self.bot_token_starbright.get_secret_value())
    
    @property
    def luna_configured(self) -> bool:
        return bool(self.bot_token_luna.get_secret_value())


class ContentSettings(BaseModel):
    """Content storage paths"""
    
    raw_path: str = "content/raw"
    final_path: str = "content/final"
    generated_path: str = "content/generated"
    archives_path: str = "content/archives"
    references_path: str = "content/references"
    telegram_path: str = "content/telegram"


class AppSettings(BaseModel):
    """Main application settings"""
    
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    session_secret: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("SESSION_SECRET", "")))
    
    api: APISettings = Field(default_factory=APISettings)
    stripe: StripeSettings = Field(default_factory=StripeSettings)
    twitter: TwitterSettings = Field(default_factory=TwitterSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    content: ContentSettings = Field(default_factory=ContentSettings)
    
    @property
    def replit_domains(self) -> list:
        """Get Replit domains for URL construction"""
        domains = os.environ.get("REPLIT_DOMAINS", "")
        return [d.strip() for d in domains.split(",") if d.strip()]
    
    @property
    def base_url(self) -> str:
        """Get base URL for the application"""
        domains = self.replit_domains
        return f"https://{domains[0]}" if domains else "https://localhost:5000"


@lru_cache()
def get_settings() -> AppSettings:
    """Get cached application settings singleton"""
    settings = AppSettings()
    logger.info("Application settings loaded")
    return settings


settings = get_settings()
