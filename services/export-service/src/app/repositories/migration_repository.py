"""
Migration repository for database operations.

Handles all migration job-related database queries.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.migration_job import MigrationJob


class MigrationRepository:
    """
    Data access layer for MigrationJob model.

    All methods operate on the async session passed in.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, migration_id: str) -> Optional[MigrationJob]:
        """
        Get migration job by ID.

        Args:
            migration_id: UUID string of the migration job

        Returns:
            MigrationJob if found, None otherwise
        """
        result = await self.db.execute(
            select(MigrationJob).where(MigrationJob.id == migration_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_workspace(
        self, migration_id: str, workspace_id: str
    ) -> Optional[MigrationJob]:
        """
        Get migration job by ID with workspace validation.

        Args:
            migration_id: UUID string of the migration job
            workspace_id: UUID string of the workspace (multi-tenancy)

        Returns:
            MigrationJob if found and belongs to workspace, None otherwise
        """
        result = await self.db.execute(
            select(MigrationJob)
            .where(MigrationJob.id == migration_id)
            .where(MigrationJob.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None,
        platform_filter: Optional[str] = None,
    ) -> list[MigrationJob]:
        """
        List migration jobs for a workspace with pagination.

        Args:
            workspace_id: UUID string of the workspace
            limit: Maximum number of results to return
            offset: Number of results to skip
            status_filter: Optional status to filter by (pending, processing, completed, failed, cancelled)
            platform_filter: Optional platform to filter by (pixieset, pic-time, shootproof, zenfolio, smugmug)

        Returns:
            List of MigrationJob instances
        """
        query = (
            select(MigrationJob)
            .where(MigrationJob.workspace_id == workspace_id)
            .order_by(MigrationJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if status_filter:
            query = query.where(MigrationJob.status == status_filter)

        if platform_filter:
            query = query.where(MigrationJob.platform == platform_filter)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[MigrationJob]:
        """
        List migration jobs created by a user.

        Args:
            user_id: UUID string of the user
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of MigrationJob instances
        """
        result = await self.db.execute(
            select(MigrationJob)
            .where(MigrationJob.user_id == user_id)
            .order_by(MigrationJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create(
        self,
        workspace_id: str,
        user_id: str,
        platform: str,
        credentials: dict,
        options: Optional[dict] = None,
    ) -> MigrationJob:
        """
        Create a new migration job.

        Args:
            workspace_id: UUID of the workspace
            user_id: UUID of the user creating the migration
            platform: Source platform (pixieset, pic-time, shootproof, zenfolio, smugmug)
            credentials: Platform credentials (API keys, tokens, etc.)
            options: Optional migration options (gallery_ids, import_metadata, etc.)

        Returns:
            Created MigrationJob instance
        """
        migration_job = MigrationJob(
            workspace_id=workspace_id,
            user_id=user_id,
            platform=platform,
            status="pending",
            credentials=credentials,
            options=options or {},
            total_assets=0,
            processed_assets=0,
            total_galleries=0,
            processed_galleries=0,
        )

        self.db.add(migration_job)
        await self.db.flush()
        await self.db.refresh(migration_job)
        return migration_job

    async def update(self, migration_id: str, **kwargs) -> Optional[MigrationJob]:
        """
        Update migration job fields.

        Args:
            migration_id: UUID of migration job to update
            **kwargs: Fields to update

        Returns:
            Updated MigrationJob if found, None otherwise
        """
        # Filter out None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        if not update_data:
            return await self.get_by_id(migration_id)

        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.db.execute(
            update(MigrationJob)
            .where(MigrationJob.id == migration_id)
            .values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_id(migration_id)

    async def update_status(
        self, migration_id: str, status: str, error_message: Optional[str] = None
    ) -> Optional[MigrationJob]:
        """
        Update migration job status.

        Args:
            migration_id: UUID of migration job
            status: New status (pending, processing, completed, failed, cancelled)
            error_message: Optional error message if status is failed

        Returns:
            Updated MigrationJob if found, None otherwise
        """
        now = datetime.now(timezone.utc)
        update_data = {
            "status": status,
            "updated_at": now,
        }

        if error_message:
            update_data["error_message"] = error_message

        if status == "completed":
            update_data["completed_at"] = now

        await self.db.execute(
            update(MigrationJob)
            .where(MigrationJob.id == migration_id)
            .values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_id(migration_id)

    async def update_progress(
        self,
        migration_id: str,
        processed_assets: Optional[int] = None,
        processed_galleries: Optional[int] = None,
        total_assets: Optional[int] = None,
        total_galleries: Optional[int] = None,
    ) -> Optional[MigrationJob]:
        """
        Update migration job progress.

        Args:
            migration_id: UUID of migration job
            processed_assets: Number of assets processed so far
            processed_galleries: Number of galleries processed so far
            total_assets: Total number of assets to process
            total_galleries: Total number of galleries to process

        Returns:
            Updated MigrationJob if found, None otherwise
        """
        update_data = {"updated_at": datetime.now(timezone.utc)}

        if processed_assets is not None:
            update_data["processed_assets"] = processed_assets

        if processed_galleries is not None:
            update_data["processed_galleries"] = processed_galleries

        if total_assets is not None:
            update_data["total_assets"] = total_assets

        if total_galleries is not None:
            update_data["total_galleries"] = total_galleries

        await self.db.execute(
            update(MigrationJob)
            .where(MigrationJob.id == migration_id)
            .values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_id(migration_id)

    async def mark_completed(
        self, migration_id: str
    ) -> Optional[MigrationJob]:
        """
        Mark migration job as completed.

        Args:
            migration_id: UUID of migration job

        Returns:
            Updated MigrationJob if found, None otherwise
        """
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(MigrationJob)
            .where(MigrationJob.id == migration_id)
            .values(
                status="completed",
                completed_at=now,
                updated_at=now,
            )
        )
        await self.db.flush()
        return await self.get_by_id(migration_id)

    async def mark_failed(
        self, migration_id: str, error_message: str
    ) -> Optional[MigrationJob]:
        """
        Mark migration job as failed with error message.

        Args:
            migration_id: UUID of migration job
            error_message: Description of the failure

        Returns:
            Updated MigrationJob if found, None otherwise
        """
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(MigrationJob)
            .where(MigrationJob.id == migration_id)
            .values(
                status="failed",
                error_message=error_message,
                updated_at=now,
            )
        )
        await self.db.flush()
        return await self.get_by_id(migration_id)

    async def cancel(self, migration_id: str) -> Optional[MigrationJob]:
        """
        Cancel a pending or processing migration job.

        Args:
            migration_id: UUID of migration job

        Returns:
            Updated MigrationJob if found, None otherwise
        """
        await self.db.execute(
            update(MigrationJob)
            .where(MigrationJob.id == migration_id)
            .where(MigrationJob.status.in_(["pending", "processing"]))
            .values(
                status="cancelled",
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()
        return await self.get_by_id(migration_id)

    async def delete_old_jobs(self, before_date: datetime) -> int:
        """
        Delete old completed migration jobs.

        Args:
            before_date: Delete jobs completed before this date

        Returns:
            Number of jobs deleted
        """
        result = await self.db.execute(
            delete(MigrationJob)
            .where(MigrationJob.completed_at < before_date)
            .where(MigrationJob.status == "completed")
        )
        await self.db.flush()
        return result.rowcount
