"""
API v1 router aggregation.

Combines all endpoint routers under /api/v1/export prefix.
"""

from fastapi import APIRouter

from src.app.api.v1.export import router as export_router
from src.app.api.v1.migration import router as migration_router

# Create main v1 router
api_router = APIRouter()

# Include export router
api_router.include_router(
    export_router,
    prefix="",
    tags=["export"],
)

# Include migration router
api_router.include_router(
    migration_router,
    prefix="/migration",
    tags=["migration"],
)
