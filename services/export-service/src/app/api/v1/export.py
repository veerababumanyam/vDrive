"""
Export API endpoints.

Handles bulk export job creation, listing, status checking, and cancellation.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.middleware.auth import CurrentUser, get_current_user
from src.app.schemas.export import (
    ExportCreateRequest,
    ExportListResponse,
    ExportResponse,
    ExportStatusResponse,
)
from src.app.services.export_service import (
    ConcurrentExportLimitError,
    ExportService,
    NotFoundError,
    PermissionError,
    ValidationError,
)
from src.app.services.storage_service import StorageService

router = APIRouter(tags=["export"])


@router.post(
    "/jobs",
    response_model=ExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create export job",
    description="Create a new export job for workspace, gallery, or selection of assets",
    responses={
        201: {"description": "Export job created successfully"},
        400: {"description": "Validation error"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        409: {"description": "Concurrent export limit exceeded"},
    },
)
async def create_export_job(
    request: ExportCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportResponse:
    """
    Create a new export job.

    Supports three export types:
    - **workspace**: Export all assets in the workspace
    - **gallery**: Export specific galleries (requires gallery_ids in options)
    - **selection**: Export specific assets (requires asset_ids in options)

    Export process:
    1. Creates export job record with status "pending"
    2. Validates export options and checks concurrent limits
    3. Dispatches Celery task for async processing (Phase 3)
    4. Returns job details with progress tracking URL

    Rate limited to prevent abuse.
    """
    if not current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "NoWorkspace",
                "message": "User must have an active workspace to create exports",
            },
        )

    service = ExportService(db, StorageService())

    try:
        return await service.create_export_job(
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
    except ConcurrentExportLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "ConcurrentExportLimitExceeded",
                "message": str(e),
            },
        )


@router.get(
    "/jobs",
    response_model=ExportListResponse,
    summary="List export jobs",
    description="List all export jobs for the current user's workspace",
    responses={
        200: {"description": "List of export jobs"},
        401: {"description": "Authentication required"},
    },
)
async def list_export_jobs(
    status_filter: Optional[str] = Query(
        None,
        description="Filter by status (pending, processing, completed, failed, cancelled)",
        examples=["completed"],
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportListResponse:
    """
    List export jobs for current workspace.

    Returns paginated list of export jobs with optional status filter.
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

    service = ExportService(db)
    return await service.list_export_jobs(
        workspace_id=current_user.workspace_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=ExportStatusResponse,
    summary="Get export job status",
    description="Get detailed status of a specific export job",
    responses={
        200: {"description": "Export job details"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {"description": "Export job not found"},
    },
)
async def get_export_job_status(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExportStatusResponse:
    """
    Get export job status and progress.

    Returns detailed information including:
    - Job status (pending, processing, completed, failed, cancelled)
    - Progress percentage
    - Download URL (when completed)
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

    service = ExportService(db)

    try:
        return await service.get_export_job(
            job_id=job_id,
            workspace_id=current_user.workspace_id,
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": "Export job not found",
            },
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "PermissionDenied",
                "message": "You do not have permission to access this export job",
            },
        )


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel export job",
    description="Cancel a pending or processing export job",
    responses={
        204: {"description": "Export job cancelled successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {"description": "Export job not found"},
        409: {"description": "Export job cannot be cancelled (already completed or failed)"},
    },
)
async def cancel_export_job(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Cancel an export job.

    Only pending or processing jobs can be cancelled.
    Completed, failed, or already cancelled jobs cannot be cancelled.

    The Celery worker will detect the cancellation and stop processing.
    """
    if not current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "NoWorkspace",
                "message": "User must have an active workspace",
            },
        )

    service = ExportService(db)

    try:
        await service.cancel_export_job(
            job_id=job_id,
            workspace_id=current_user.workspace_id,
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": "Export job not found",
            },
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "PermissionDenied",
                "message": "You do not have permission to cancel this export job",
            },
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "CannotCancel",
                "message": str(e),
            },
        )
