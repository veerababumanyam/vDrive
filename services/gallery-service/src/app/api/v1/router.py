"""Main API router aggregating all v1 endpoints"""

from fastapi import APIRouter

from src.app.api.v1 import batch, preview, public_access, websocket

# Create main router
api_router = APIRouter()

# Include routers
api_router.include_router(
    public_access.router,
    prefix="/public",
    tags=["Public Access"],
)

# WebSocket router for real-time updates
api_router.include_router(
    websocket.router,
    tags=["WebSocket"],
)

# Preview mode router
api_router.include_router(
    preview.router,
    tags=["Preview"],
)

# Batch operations router
api_router.include_router(
    batch.router,
    tags=["Batch Operations"],
)
