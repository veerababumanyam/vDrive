"""
Migration API endpoints.

Handles migration job creation, listing, status checking, and cancellation
for importing data from competitor platforms.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.middleware.auth import CurrentUser, get_current_user
from src.app.schemas.migration import (
    MigrationCreateRequest,
    MigrationListResponse,
    MigrationResponse,
    MigrationStatusResponse,
)
from src.app.services.migration_service import (
    MigrationService,
    NotFoundError,
    PermissionError,
    UnsupportedPlatformError,
    ValidationError,
)

router = APIRouter(tags=["migration"])


@router.post(
    "/jobs",
    response_model=MigrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create migration job",
    description="Create a new migration job to import data from competitor platforms",
    responses={
        201: {"description": "Migration job created successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        422: {"description": "Unsupported platform"},
    },
)
async def create_migration_job(
    request: MigrationCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MigrationResponse:
    """
    Create a new migration job.

    Supports importing from:
    - **pixieset**: Requires API key
    - **pic-time**: Requires username and password
    - **shootproof**: Requires username and password
    - **zenfolio**: Requires API key and secret (coming soon)
    - **smugmug**: Requires API key and secret (coming soon)

    Migration process:
    1. Creates migration job record with status "pending"
    2. Validates platform credentials
    3. Dispatches Celery task for async processing (Phase 3)
    4. Returns job details with progress tracking URL

    Rate limited to prevent abuse.
    """
    if not current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "NoWorkspace",
                "message": "User must have an active workspace to create migrations",
            },
        )

    service = MigrationService(db)

    try:
        return await service.create_migration_job(
            request=request,
            workspace_id=current_user.workspace_id,
            user_id=current_user.user_id,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ValidationError",
                "message": str(e),
            },
        )
    except UnsupportedPlatformError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "UnsupportedPlatform",
                "message": str(e),
            },
        )


@router.get(
    "/jobs",
    response_model=MigrationListResponse,
    summary="List migration jobs",
    description="List all migration jobs for the current user's workspace",
    responses={
        200: {"description": "List of migration jobs"},
        401: {"description": "Authentication required"},
    },
)
async def list_migration_jobs(
    status_filter: Optional[str] = Query(
        None,
        description="Filter by status (pending, processing, completed, failed, cancelled)",
        examples=["completed"],
    ),
    platform_filter: Optional[str] = Query(
        None,
        description="Filter by platform (pixieset, pic-time, shootproof, zenfolio, smugmug)",
        examples=["pixieset"],
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MigrationListResponse:
    """
    List migration jobs for current workspace.

    Returns paginated list of migration jobs with optional filters.
    Results are ordered by created_at descending (newest first).
    """
    if not current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "NoWorkspace",
                "message": "User must have an active workspace",
            },
        )

    service = MigrationService(db)
    return await service.list_migration_jobs(
        workspace_id=current_user.workspace_id,
        status_filter=status_filter,
        platform_filter=platform_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=MigrationStatusResponse,
    summary="Get migration job status",
    description="Get detailed status of a specific migration job",
    responses={
        200: {"description": "Migration job details"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {"description": "Migration job not found"},
    },
)
async def get_migration_job_status(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MigrationStatusResponse:
    """
    Get migration job status and progress.

    Returns detailed information including:
    - Job status (pending, processing, completed, failed, cancelled)
    - Progress percentage
    - Total and processed assets/galleries
    - Error message (if failed)

    Frontend should poll this endpoint while job is processing.
    """
    if not current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "NoWorkspace",
                "message": "User must have an active workspace",
            },
        )

    service = MigrationService(db)

    try:
        return await service.get_migration_job(
            migration_id=job_id,
            workspace_id=current_user.workspace_id,
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": "Migration job not found",
            },
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "PermissionDenied",
                "message": "You do not have permission to access this migration job",
            },
        )


@router.delete(
    "/jobs/{job_id}",
    response_model=MigrationResponse,
    summary="Cancel migration job",
    description="Cancel a pending or processing migration job",
    responses={
        200: {"description": "Migration job cancelled successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {"description": "Migration job not found"},
        400: {"description": "Migration job cannot be cancelled"},
    },
)
async def cancel_migration_job(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MigrationResponse:
    """
    Cancel a migration job.

    Only pending or processing jobs can be cancelled.
    Completed, failed, or already cancelled jobs cannot be cancelled.

    This will:
    1. Stop the migration processing (if in progress)
    2. Mark the job as cancelled
    3. Clean up any temporary resources
    """
    if not current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "NoWorkspace",
                "message": "User must have an active workspace",
            },
        )

    service = MigrationService(db)

    try:
        return await service.cancel_migration_job(
            migration_id=job_id,
            workspace_id=current_user.workspace_id,
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": "Migration job not found",
            },
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "PermissionDenied",
                "message": "You do not have permission to access this migration job",
            },
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ValidationError",
                "message": str(e),
            },
        )
