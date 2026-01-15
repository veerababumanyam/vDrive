"""API v1 router aggregation."""

from fastapi import APIRouter

from .search import router as search_router

# Create v1 router
router = APIRouter(prefix="/api/v1")

# Include all sub-routers
router.include_router(search_router)

__all__ = ["router"]
