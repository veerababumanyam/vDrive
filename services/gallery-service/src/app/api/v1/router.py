"""Main API router aggregating all v1 endpoints"""

from fastapi import APIRouter

# Create main router
api_router = APIRouter()

# TODO: Import and include routers as they are implemented
# from src.app.api.v1 import public_access, gallery_viewing, batch_operations

# api_router.include_router(
#     public_access.router,
#     prefix="/public",
#     tags=["public"],
# )
