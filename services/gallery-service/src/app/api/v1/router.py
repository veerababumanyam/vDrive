"""Main API router aggregating all v1 endpoints"""

from fastapi import APIRouter

from src.app.api.v1 import public_access

# Create main router
api_router = APIRouter()

# Include routers
api_router.include_router(
    public_access.router,
    prefix="/public",
    tags=["Public Access"],
)

# TODO: Add more routers as they are implemented
# from src.app.api.v1 import gallery_viewing, batch_operations
