"""API routers for the AIA Engine"""
from .admin_routes import router as admin_router
from .payment_routes import router as payment_router
from .telegram_api_routes import router as telegram_api_router
from .micro_loop_routes import router as micro_loop_router
from .webchat_routes import router as webchat_router
from .gallery_routes import router as gallery_router
from .twitter_routes import router as twitter_router
from .seedream4_routes import router as seedream4_router
from .unified_routes import router as unified_router
from .workflow_routes import router as workflow_router
from .object_storage_routes import router as object_storage_router

__all__ = [
    "admin_router",
    "payment_router", 
    "telegram_api_router",
    "micro_loop_router",
    "webchat_router",
    "gallery_router",
    "twitter_router",
    "seedream4_router",
    "unified_router",
    "workflow_router",
    "object_storage_router",
]
