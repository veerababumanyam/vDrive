"""
Migration service for importing data from competitor platforms.

Handles migration job creation, validation, and platform adapter orchestration.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.migration_job import MigrationJob
from src.app.repositories.migration_repository import MigrationRepository
from src.app.schemas.migration import (
    MigrationCreateRequest,
    MigrationListResponse,
    MigrationResponse,
)
from src.app.services.adapters import PlatformAdapter
from src.app.services.adapters.pictime_adapter import PictimeAdapter
from src.app.services.adapters.pixieset_adapter import PixiesetAdapter
from src.app.services.adapters.shootproof_adapter import ShootproofAdapter

logger = logging.getLogger(__name__)


class MigrationServiceError(Exception):
    """Base exception for migration service errors."""

    pass


class ValidationError(MigrationServiceError):
    """Raised when validation fails."""

    pass


class NotFoundError(MigrationServiceError):
    """Raised when resource is not found."""

    pass


class PermissionError(MigrationServiceError):
    """Raised when user lacks permission to access resource."""

    pass


class UnsupportedPlatformError(MigrationServiceError):
    """Raised when platform is not supported."""

    pass


class MigrationService:
    """
    Service for migration job business logic.

    Handles migration job creation, validation, listing, and platform adapter
    creation. Enforces multi-tenancy and provides helper methods for migration
    processing.
    """

    # Supported platform adapters
    PLATFORM_ADAPTERS = {
        "pixieset": PixiesetAdapter,
        "pic-time": PictimeAdapter,
        "shootproof": ShootproofAdapter,
        # TODO: Add Zenfolio and SmugMug adapters when implemented
        # "zenfolio": ZenfolioAdapter,
        # "smugmug": SmugmugAdapter,
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize migration service.

        Args:
            db: Database session
        """
        self.db = db
        self.migration_repo = MigrationRepository(db)

    async def create_migration_job(
        self,
        request: MigrationCreateRequest,
        workspace_id: str,
        user_id: str,
    ) -> MigrationResponse:
        """
        Create a new migration job.

        Steps:
        1. Validate migration request (platform, credentials)
        2. Create migration job record
        3. Return migration response

        Args:
            request: Migration creation request
            workspace_id: UUID of workspace (multi-tenancy)
            user_id: UUID of user creating migration

        Returns:
            MigrationResponse with job details

        Raises:
            UnsupportedPlatformError: If platform is not supported
            ValidationError: If request validation fails
        """
        # 1. Validate platform
        if request.platform not in self.PLATFORM_ADAPTERS:
            raise UnsupportedPlatformError(
                f"Platform '{request.platform}' is not supported yet. "
                f"Supported platforms: {', '.join(self.PLATFORM_ADAPTERS.keys())}"
            )

        # 2. Validate credentials (basic validation, detailed validation happens during processing)
        await self._validate_migration_request(request)

        # 3. Create migration job record
        migration_job = await self.migration_repo.create(
            workspace_id=workspace_id,
            user_id=user_id,
            platform=request.platform,
            credentials=request.credentials,
            options=request.options or {},
        )

        # 4. Commit transaction
        await self.db.commit()
        await self.db.refresh(migration_job)

        logger.info(
            f"Created migration job {migration_job.id}",
            extra={
                "migration_id": migration_job.id,
                "workspace_id": workspace_id,
                "user_id": user_id,
                "platform": request.platform,
            },
        )

        return self._migration_job_to_response(migration_job)

    async def get_migration_job(
        self,
        migration_id: str,
        workspace_id: str,
    ) -> MigrationResponse:
        """
        Get migration job by ID with workspace validation.

        Args:
            migration_id: UUID of migration job
            workspace_id: UUID of workspace (multi-tenancy)

        Returns:
            MigrationResponse with job details

        Raises:
            NotFoundError: If migration job not found or doesn't belong to workspace
        """
        migration_job = await self.migration_repo.get_by_id_and_workspace(
            migration_id=migration_id,
            workspace_id=workspace_id,
        )

        if not migration_job:
            raise NotFoundError(
                f"Migration job {migration_id} not found in workspace {workspace_id}"
            )

        return self._migration_job_to_response(migration_job)

    async def list_migration_jobs(
        self,
        workspace_id: str,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        platform_filter: Optional[str] = None,
    ) -> MigrationListResponse:
        """
        List migration jobs for a workspace with pagination.

        Args:
            workspace_id: UUID of workspace (multi-tenancy)
            page: Page number (1-indexed)
            page_size: Number of items per page
            status_filter: Optional status to filter by
            platform_filter: Optional platform to filter by

        Returns:
            MigrationListResponse with paginated results
        """
        # Calculate offset
        offset = (page - 1) * page_size

        # Get jobs from repository
        jobs = await self.migration_repo.list_by_workspace(
            workspace_id=workspace_id,
            limit=page_size,
            offset=offset,
            status_filter=status_filter,
            platform_filter=platform_filter,
        )

        # Convert to response models
        job_responses = [self._migration_job_to_response(job) for job in jobs]

        # Note: For production, we should also get total count for pagination
        # For now, we'll use the number of returned jobs
        total = len(jobs)

        return MigrationListResponse(
            jobs=job_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def cancel_migration_job(
        self,
        migration_id: str,
        workspace_id: str,
    ) -> MigrationResponse:
        """
        Cancel a pending or processing migration job.

        Args:
            migration_id: UUID of migration job
            workspace_id: UUID of workspace (multi-tenancy)

        Returns:
            MigrationResponse with updated job details

        Raises:
            NotFoundError: If migration job not found or doesn't belong to workspace
            ValidationError: If migration job cannot be cancelled
        """
        # First verify the job exists and belongs to workspace
        migration_job = await self.migration_repo.get_by_id_and_workspace(
            migration_id=migration_id,
            workspace_id=workspace_id,
        )

        if not migration_job:
            raise NotFoundError(
                f"Migration job {migration_id} not found in workspace {workspace_id}"
            )

        # Check if job can be cancelled
        if migration_job.status not in ["pending", "processing"]:
            raise ValidationError(
                f"Cannot cancel migration job with status '{migration_job.status}'"
            )

        # Cancel the job
        cancelled_job = await self.migration_repo.cancel(migration_id=migration_id)

        if not cancelled_job:
            raise NotFoundError(f"Migration job {migration_id} not found after cancel")

        # Commit transaction
        await self.db.commit()
        await self.db.refresh(cancelled_job)

        logger.info(
            f"Cancelled migration job {migration_id}",
            extra={
                "migration_id": migration_id,
                "workspace_id": workspace_id,
            },
        )

        return self._migration_job_to_response(cancelled_job)

    def create_platform_adapter(
        self,
        platform: str,
        credentials: dict,
    ) -> PlatformAdapter:
        """
        Create platform adapter instance.

        Args:
            platform: Platform name (pixieset, pic-time, shootproof, etc.)
            credentials: Platform credentials

        Returns:
            PlatformAdapter instance for the specified platform

        Raises:
            UnsupportedPlatformError: If platform is not supported
        """
        adapter_class = self.PLATFORM_ADAPTERS.get(platform)
        if not adapter_class:
            raise UnsupportedPlatformError(
                f"Platform '{platform}' is not supported yet. "
                f"Supported platforms: {', '.join(self.PLATFORM_ADAPTERS.keys())}"
            )

        return adapter_class(credentials)

    async def _validate_migration_request(
        self,
        request: MigrationCreateRequest,
    ) -> None:
        """
        Validate migration request.

        Args:
            request: Migration creation request

        Raises:
            ValidationError: If validation fails
        """
        # Basic validation is already done by Pydantic
        # Add any additional business logic validation here

        # Verify credentials have required fields (already done by Pydantic validator)
        logger.debug(
            f"Validating migration request: {request.platform}",
            extra={"platform": request.platform, "options": request.options},
        )

    def _migration_job_to_response(
        self,
        migration_job: MigrationJob,
    ) -> MigrationResponse:
        """
        Convert MigrationJob model to MigrationResponse schema.

        Note: We exclude credentials from the response for security.

        Args:
            migration_job: MigrationJob database model

        Returns:
            MigrationResponse Pydantic schema
        """
        return MigrationResponse(
            id=migration_job.id,
            workspace_id=migration_job.workspace_id,
            user_id=migration_job.user_id,
            platform=migration_job.platform,
            status=migration_job.status,
            options=migration_job.options,
            total_assets=migration_job.total_assets,
            processed_assets=migration_job.processed_assets,
            total_galleries=migration_job.total_galleries,
            processed_galleries=migration_job.processed_galleries,
            progress_percentage=migration_job.progress_percentage,
            error_message=migration_job.error_message,
            created_at=migration_job.created_at,
            updated_at=migration_job.updated_at,
            completed_at=migration_job.completed_at,
        )
