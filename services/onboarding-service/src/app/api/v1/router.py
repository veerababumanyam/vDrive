"""
API v1 router aggregation.

Combines all endpoint routers under /api/v1/onboarding prefix.
"""

from fastapi import APIRouter

from src.app.api.v1.auth import router as auth_router
from src.app.api.v1.login import router as login_router
from src.app.api.v1.oauth import router as oauth_router
from src.app.api.v1.onboarding import router as onboarding_router
from src.app.api.v1.registration import router as registration_router
from src.app.api.v1.verification import router as verification_router
from src.app.api.v1.workspace import router as workspace_router

# Create main v1 router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(
    auth_router,
    prefix="",
    tags=["auth"],
)

api_router.include_router(
    login_router,
    prefix="",
    tags=["login"],
)

api_router.include_router(
    registration_router,
    prefix="",
    tags=["registration"],
)

api_router.include_router(
    verification_router,
    prefix="",
    tags=["verification"],
)

api_router.include_router(
    oauth_router,
    prefix="",
    tags=["oauth"],
)

api_router.include_router(
    workspace_router,
    prefix="",
    tags=["workspace"],
)

api_router.include_router(
    onboarding_router,
    prefix="",
    tags=["onboarding"],
)
