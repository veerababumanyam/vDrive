"""API v1 router aggregation."""

from fastapi import APIRouter

from .captions import router as captions_router
from .chat import router as chat_router
from .search import router as search_router

# Create v1 router
router = APIRouter(prefix="/api/v1")

# Include all sub-routers
router.include_router(captions_router)
router.include_router(chat_router)
router.include_router(search_router)

__all__ = ["router"]
