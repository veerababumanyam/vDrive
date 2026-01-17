"""
Export service for bulk export business logic.

Handles export job creation, validation, and management.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.models.export_job import ExportJob
from src.app.repositories.export_repository import ExportRepository
from src.app.schemas.export import (
    ExportCreateRequest,
    ExportListResponse,
    ExportResponse,
)
from src.app.services.storage_service import StorageService
from src.app.workers.export_tasks import process_export_job

logger = logging.getLogger(__name__)


class ExportServiceError(Exception):
    """Base exception for export service errors."""

    pass


class ConcurrentExportLimitError(ExportServiceError):
    """Raised when workspace exceeds concurrent export limit."""

    pass


class ValidationError(ExportServiceError):
    """Raised when validation fails."""

    pass


class NotFoundError(ExportServiceError):
    """Raised when resource is not found."""

    pass


class PermissionError(ExportServiceError):
    """Raised when user lacks permission to access resource."""

    pass


class ExportService:
    """
    Service for export job business logic.

    Handles export job creation, validation, listing, and cancellation.
    Enforces multi-tenancy and concurrent export limits.
    """

    def __init__(
        self,
        db: AsyncSession,
        storage_service: Optional[StorageService] = None,
    ):
        """
        Initialize export service.

        Args:
            db: Database session
            storage_service: Optional storage service (defaults to new instance)
        """
        self.db = db
        self.export_repo = ExportRepository(db)
        self.storage_service = storage_service or StorageService()

    async def create_export_job(
        self,
        request: ExportCreateRequest,
        workspace_id: str,
        user_id: str,
    ) -> ExportResponse:
        """
        Create a new export job.

        Steps:
        1. Validate export request options
        2. Check concurrent export limit
        3. Estimate total assets (if possible)
        4. Create export job record
        5. Calculate expiration date
        6. Return export response

        Args:
            request: Export creation request
            workspace_id: UUID of workspace (multi-tenancy)
            user_id: UUID of user creating export

        Returns:
            ExportResponse with job details

        Raises:
            ConcurrentExportLimitError: If workspace exceeds concurrent export limit
            ValidationError: If request validation fails
        """
        # 1. Validate export type and options
        await self._validate_export_request(request)

        # 2. Check concurrent export limit
        await self._check_concurrent_limit(workspace_id)

        # 3. Estimate total assets (placeholder - will be calculated by worker)
        total_assets = 0  # Worker will update this when it starts processing

        # 4. Create export job record
        export_job = await self.export_repo.create(
            workspace_id=workspace_id,
            user_id=user_id,
            export_type=request.export_type,
            options=request.options or {},
            total_assets=total_assets,
        )

        # 5. Commit transaction
        await self.db.commit()
        await self.db.refresh(export_job)

        # 6. Dispatch Celery task for async processing
        task_result = self._dispatch_export_task(export_job.id)

        logger.info(
            f"Created export job {export_job.id}",
            extra={
                "export_id": export_job.id,
                "workspace_id": workspace_id,
                "user_id": user_id,
                "export_type": request.export_type,
                "celery_task_id": task_result.id if task_result else None,
            },
        )

        return self._export_job_to_response(export_job)

    async def get_export_job(
        self,
        export_id: str,
        workspace_id: str,
    ) -> ExportResponse:
        """
        Get export job by ID with workspace validation.

        Args:
            export_id: UUID of export job
            workspace_id: UUID of workspace (multi-tenancy)

        Returns:
            ExportResponse with job details

        Raises:
            NotFoundError: If export job not found or doesn't belong to workspace
        """
        export_job = await self.export_repo.get_by_id_and_workspace(
            export_id=export_id,
            workspace_id=workspace_id,
        )

        if not export_job:
            raise NotFoundError(
                f"Export job {export_id} not found in workspace {workspace_id}"
            )

        return self._export_job_to_response(export_job)

    async def list_export_jobs(
        self,
        workspace_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
    ) -> ExportListResponse:
        """
        List export jobs for a workspace with pagination.

        Args:
            workspace_id: UUID of workspace (multi-tenancy)
            page: Page number (1-indexed)
            page_size: Number of items per page
            status_filter: Optional status to filter by

        Returns:
            ExportListResponse with paginated results
        """
        # Calculate offset
        offset = (page - 1) * page_size

        # Get jobs from repository
        jobs = await self.export_repo.list_by_workspace(
            workspace_id=workspace_id,
            limit=page_size,
            offset=offset,
            status_filter=status_filter,
        )

        # Convert to response models
        job_responses = [self._export_job_to_response(job) for job in jobs]

        # Note: For production, we should also get total count for pagination
        # For now, we'll use the number of returned jobs
        total = len(jobs)

        return ExportListResponse(
            jobs=job_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def cancel_export_job(
        self,
        export_id: str,
        workspace_id: str,
    ) -> ExportResponse:
        """
        Cancel a pending or processing export job.

        Args:
            export_id: UUID of export job
            workspace_id: UUID of workspace (multi-tenancy)

        Returns:
            ExportResponse with updated job details

        Raises:
            NotFoundError: If export job not found or doesn't belong to workspace
            ValidationError: If export job cannot be cancelled
        """
        # First verify the job exists and belongs to workspace
        export_job = await self.export_repo.get_by_id_and_workspace(
            export_id=export_id,
            workspace_id=workspace_id,
        )

        if not export_job:
            raise NotFoundError(
                f"Export job {export_id} not found in workspace {workspace_id}"
            )

        # Check if job can be cancelled
        if export_job.status not in ["pending", "processing"]:
            raise ValidationError(
                f"Cannot cancel export job with status '{export_job.status}'"
            )

        # Cancel the job
        cancelled_job = await self.export_repo.cancel(export_id=export_id)

        if not cancelled_job:
            raise NotFoundError(f"Export job {export_id} not found after cancel")

        # Commit transaction
        await self.db.commit()
        await self.db.refresh(cancelled_job)

        logger.info(
            f"Cancelled export job {export_id}",
            extra={
                "export_id": export_id,
                "workspace_id": workspace_id,
            },
        )

        # Cancel Celery task if running
        self._cancel_export_task(export_id)

        return self._export_job_to_response(cancelled_job)

    async def cleanup_expired_exports(self) -> int:
        """
        Clean up expired export files and database records.

        This should be run periodically (e.g., via cron job or scheduled task).

        Returns:
            Number of exports cleaned up
        """
        now = datetime.now(timezone.utc)

        # Delete expired export jobs from database
        deleted_count = await self.export_repo.delete_expired(before_date=now)

        # Commit transaction
        await self.db.commit()

        logger.info(f"Cleaned up {deleted_count} expired export jobs")

        return deleted_count

    async def _validate_export_request(
        self,
        request: ExportCreateRequest,
    ) -> None:
        """
        Validate export request.

        Args:
            request: Export creation request

        Raises:
            ValidationError: If validation fails
        """
        # Basic validation is already done by Pydantic
        # Add any additional business logic validation here

        # For now, just log the validation
        logger.debug(
            f"Validating export request: {request.export_type}",
            extra={"export_type": request.export_type, "options": request.options},
        )

    async def _check_concurrent_limit(
        self,
        workspace_id: str,
    ) -> None:
        """
        Check if workspace has exceeded concurrent export limit.

        Args:
            workspace_id: UUID of workspace

        Raises:
            ConcurrentExportLimitError: If limit exceeded
        """
        # Get active exports (pending or processing) for workspace
        active_exports = await self.export_repo.list_by_workspace(
            workspace_id=workspace_id,
            limit=settings.MAX_CONCURRENT_EXPORTS + 1,
            offset=0,
            status_filter=None,  # We'll filter manually
        )

        # Count pending/processing exports
        active_count = sum(
            1
            for job in active_exports
            if job.status in ["pending", "processing"]
        )

        if active_count >= settings.MAX_CONCURRENT_EXPORTS:
            raise ConcurrentExportLimitError(
                f"Workspace has reached maximum concurrent export limit "
                f"({settings.MAX_CONCURRENT_EXPORTS}). Please wait for existing exports to complete."
            )

    def _dispatch_export_task(
        self,
        export_id: str,
    ) -> Optional[AsyncResult]:
        """
        Dispatch Celery task for async export processing.

        Args:
            export_id: UUID of export job to process

        Returns:
            AsyncResult with task ID, or None if dispatch failed
        """
        try:
            # Dispatch task to Celery worker
            task_result = process_export_job.apply_async(
                args=[export_id],
                queue="exports",
                routing_key="export.process",
            )

            logger.info(
                f"Dispatched Celery task for export {export_id}",
                extra={
                    "export_id": export_id,
                    "celery_task_id": task_result.id,
                },
            )

            return task_result

        except Exception as e:
            logger.error(
                f"Failed to dispatch Celery task for export {export_id}: {e}",
                exc_info=True,
                extra={"export_id": export_id},
            )
            return None

    def _cancel_export_task(
        self,
        export_id: str,
    ) -> bool:
        """
        Cancel running Celery task for export job.

        Note: This is a best-effort operation. The task may still complete
        if it's already processing. The export job status is the source of truth.

        Args:
            export_id: UUID of export job

        Returns:
            True if cancellation was attempted, False otherwise
        """
        try:
            # In a production system, we would need to:
            # 1. Look up the Celery task ID from the export job
            # 2. Revoke the task using celery_app.control.revoke()
            #
            # For now, we'll just log the cancellation attempt.
            # The worker will check the job status before starting and
            # periodically during processing.

            logger.info(
                f"Cancellation requested for export {export_id}",
                extra={"export_id": export_id},
            )

            # TODO: Store task_id in export_job model and revoke it here
            # from src.app.workers.celery_app import celery_app
            # celery_app.control.revoke(task_id, terminate=True)

            return True

        except Exception as e:
            logger.error(
                f"Failed to cancel Celery task for export {export_id}: {e}",
                exc_info=True,
                extra={"export_id": export_id},
            )
            return False

    def _export_job_to_response(
        self,
        export_job: ExportJob,
    ) -> ExportResponse:
        """
        Convert ExportJob model to ExportResponse schema.

        Args:
            export_job: ExportJob database model

        Returns:
            ExportResponse Pydantic schema
        """
        return ExportResponse(
            id=export_job.id,
            workspace_id=export_job.workspace_id,
            user_id=export_job.user_id,
            export_type=export_job.export_type,
            status=export_job.status,
            options=export_job.options,
            total_assets=export_job.total_assets,
            processed_assets=export_job.processed_assets,
            progress_percentage=export_job.progress_percentage,
            file_url=export_job.file_url,
            file_size=export_job.file_size,
            file_key=export_job.file_key,
            error_message=export_job.error_message,
            expires_at=export_job.expires_at,
            created_at=export_job.created_at,
            updated_at=export_job.updated_at,
            completed_at=export_job.completed_at,
        )
