"""
Gallery Service API v1 Router

Main router for gallery-related endpoints.
"""

from fastapi import APIRouter

from src.app.api.v1.watermark import router as watermark_router

# Create API router
api_router = APIRouter()

# Include watermark router
api_router.include_router(
    watermark_router,
    prefix="/watermark",
    tags=["watermark"],
)


@api_router.get("/health")
async def api_health():
    """API-level health check."""
    return {"status": "ok", "api_version": "v1"}
