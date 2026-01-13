"""
Workspace API endpoints.

Handles workspace creation and slug management.
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.events.kafka_producer import KafkaProducer, get_kafka_producer
from src.app.middleware.auth import CurrentUser, get_current_user, get_verified_user
from src.app.middleware.rate_limit import rate_limit_slug_check
from src.app.schemas.workspace import (
    SlugCheckResponse,
    SlugSuggestResponse,
    WorkspaceCreateRequest,
    WorkspaceResponse,
)
from src.app.services.workspace_service import WorkspaceService

router = APIRouter(tags=["workspace"])


@router.post(
    "/workspace",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workspace",
    description="Create a new workspace for the authenticated user",
    responses={
        201: {"description": "Workspace created successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Authentication required"},
        403: {"description": "Email not verified"},
        409: {"description": "Slug already taken"},
    },
)
async def create_workspace(
    request: WorkspaceCreateRequest,
    current_user: CurrentUser = Depends(get_verified_user),
    db: AsyncSession = Depends(get_db),
    kafka_producer: KafkaProducer = Depends(get_kafka_producer),
) -> WorkspaceResponse:
    """
    Create a new workspace.

    - Requires verified email
    - Creates workspace with Pro Trial (14 days, 100GB, 500 AI credits)
    - Assigns user as workspace Owner
    - Updates onboarding progress
    """
    service = WorkspaceService(db, kafka_producer)
    return await service.create_workspace(current_user.user_id, request)


@router.get(
    "/workspace/slug-check",
    response_model=SlugCheckResponse,
    summary="Check slug availability",
    description="Check if a workspace slug is available",
    responses={
        200: {"description": "Slug availability status"},
        400: {"description": "Invalid slug format"},
        401: {"description": "Authentication required"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def check_slug_availability(
    slug: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Slug to check",
        examples=["lumina-studios"],
    ),
    _rate_limit: None = Depends(rate_limit_slug_check),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SlugCheckResponse:
    """
    Check if workspace slug is available.

    - Real-time availability check
    - Returns suggestions if slug is taken
    - Must respond under 500ms

    Rate limited to 100 checks per IP per minute.
    """
    service = WorkspaceService(db)
    return await service.check_slug_availability(slug)


@router.get(
    "/workspace/suggest-slug",
    response_model=SlugSuggestResponse,
    summary="Suggest workspace slugs",
    description="Generate available slug suggestions from business name",
    responses={
        200: {"description": "Slug suggestions"},
        401: {"description": "Authentication required"},
    },
)
async def suggest_slug(
    name: str = Query(
        ...,
        min_length=1,
        max_length=255,
        description="Business name to generate slugs from",
        examples=["Lumina Photography Studio"],
    ),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SlugSuggestResponse:
    """
    Generate available slug suggestions from business name.

    - Generates URL-safe slug from name
    - Returns up to 3 available options
    - Handles unicode characters (transliterates to ASCII)
    """
    service = WorkspaceService(db)
    return await service.suggest_available_slugs(name)
