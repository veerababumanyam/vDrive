"""API v1 router aggregation."""

from fastapi import APIRouter

from .faces import router as faces_router
from .find_me import router as find_me_router
from .people import router as people_router

# Create v1 router
router = APIRouter(prefix="/api/v1")

# Include all sub-routers
router.include_router(faces_router)
router.include_router(find_me_router)
router.include_router(people_router)

__all__ = ["router"]
