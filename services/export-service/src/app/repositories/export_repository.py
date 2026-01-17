"""
Export repository for database operations.

Handles all export job-related database queries.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.export_job import ExportJob


class ExportRepository:
    """
    Data access layer for ExportJob model.

    All methods operate on the async session passed in.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, export_id: str) -> Optional[ExportJob]:
        """
        Get export job by ID.

        Args:
            export_id: UUID string of the export job

        Returns:
            ExportJob if found, None otherwise
        """
        result = await self.db.execute(
            select(ExportJob).where(ExportJob.id == export_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_workspace(
        self, export_id: str, workspace_id: str
    ) -> Optional[ExportJob]:
        """
        Get export job by ID with workspace validation.

        Args:
            export_id: UUID string of the export job
            workspace_id: UUID string of the workspace (multi-tenancy)

        Returns:
            ExportJob if found and belongs to workspace, None otherwise
        """
        result = await self.db.execute(
            select(ExportJob)
            .where(ExportJob.id == export_id)
            .where(ExportJob.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self,
        workspace_id: str,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None,
    ) -> list[ExportJob]:
        """
        List export jobs for a workspace with pagination.

        Args:
            workspace_id: UUID string of the workspace
            limit: Maximum number of results to return
            offset: Number of results to skip
            status_filter: Optional status to filter by (pending, processing, completed, failed, cancelled)

        Returns:
            List of ExportJob instances
        """
        query = (
            select(ExportJob)
            .where(ExportJob.workspace_id == workspace_id)
            .order_by(ExportJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if status_filter:
            query = query.where(ExportJob.status == status_filter)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[ExportJob]:
        """
        List export jobs created by a user.

        Args:
            user_id: UUID string of the user
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of ExportJob instances
        """
        result = await self.db.execute(
            select(ExportJob)
            .where(ExportJob.user_id == user_id)
            .order_by(ExportJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create(
        self,
        workspace_id: str,
        user_id: str,
        export_type: str,
        options: Optional[dict] = None,
        total_assets: int = 0,
    ) -> ExportJob:
        """
        Create a new export job.

        Args:
            workspace_id: UUID of the workspace
            user_id: UUID of the user creating the export
            export_type: Type of export (workspace, gallery, selection)
            options: Optional export options (include_metadata, gallery_ids, etc.)
            total_assets: Total number of assets to export

        Returns:
            Created ExportJob instance
        """
        export_job = ExportJob(
            workspace_id=workspace_id,
            user_id=user_id,
            export_type=export_type,
            status="pending",
            options=options or {},
            total_assets=total_assets,
            processed_assets=0,
        )

        self.db.add(export_job)
        await self.db.flush()
        await self.db.refresh(export_job)
        return export_job

    async def update(self, export_id: str, **kwargs) -> Optional[ExportJob]:
        """
        Update export job fields.

        Args:
            export_id: UUID of export job to update
            **kwargs: Fields to update

        Returns:
            Updated ExportJob if found, None otherwise
        """
        # Filter out None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        if not update_data:
            return await self.get_by_id(export_id)

        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.db.execute(
            update(ExportJob)
            .where(ExportJob.id == export_id)
            .values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_id(export_id)

    async def update_status(
        self, export_id: str, status: str, error_message: Optional[str] = None
    ) -> Optional[ExportJob]:
        """
        Update export job status.

        Args:
            export_id: UUID of export job
            status: New status (pending, processing, completed, failed, cancelled)
            error_message: Optional error message if status is failed

        Returns:
            Updated ExportJob if found, None otherwise
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
            update(ExportJob)
            .where(ExportJob.id == export_id)
            .values(**update_data)
        )
        await self.db.flush()
        return await self.get_by_id(export_id)

    async def update_progress(
        self, export_id: str, processed_assets: int
    ) -> Optional[ExportJob]:
        """
        Update export job progress.

        Args:
            export_id: UUID of export job
            processed_assets: Number of assets processed so far

        Returns:
            Updated ExportJob if found, None otherwise
        """
        await self.db.execute(
            update(ExportJob)
            .where(ExportJob.id == export_id)
            .values(
                processed_assets=processed_assets,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()
        return await self.get_by_id(export_id)

    async def mark_completed(
        self,
        export_id: str,
        file_url: str,
        file_size: int,
        file_key: str,
        expires_at: datetime,
    ) -> Optional[ExportJob]:
        """
        Mark export job as completed with file information.

        Args:
            export_id: UUID of export job
            file_url: Presigned R2 download URL
            file_size: Size of export file in bytes
            file_key: R2 storage key for the file
            expires_at: When the export file will be deleted

        Returns:
            Updated ExportJob if found, None otherwise
        """
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(ExportJob)
            .where(ExportJob.id == export_id)
            .values(
                status="completed",
                file_url=file_url,
                file_size=file_size,
                file_key=file_key,
                expires_at=expires_at,
                completed_at=now,
                updated_at=now,
            )
        )
        await self.db.flush()
        return await self.get_by_id(export_id)

    async def mark_failed(
        self, export_id: str, error_message: str
    ) -> Optional[ExportJob]:
        """
        Mark export job as failed with error message.

        Args:
            export_id: UUID of export job
            error_message: Description of the failure

        Returns:
            Updated ExportJob if found, None otherwise
        """
        now = datetime.now(timezone.utc)
        await self.db.execute(
            update(ExportJob)
            .where(ExportJob.id == export_id)
            .values(
                status="failed",
                error_message=error_message,
                updated_at=now,
            )
        )
        await self.db.flush()
        return await self.get_by_id(export_id)

    async def cancel(self, export_id: str) -> Optional[ExportJob]:
        """
        Cancel a pending or processing export job.

        Args:
            export_id: UUID of export job

        Returns:
            Updated ExportJob if found, None otherwise
        """
        await self.db.execute(
            update(ExportJob)
            .where(ExportJob.id == export_id)
            .where(ExportJob.status.in_(["pending", "processing"]))
            .values(
                status="cancelled",
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()
        return await self.get_by_id(export_id)

    async def delete_expired(self, before_date: datetime) -> int:
        """
        Delete expired export jobs.

        Args:
            before_date: Delete jobs with expires_at before this date

        Returns:
            Number of jobs deleted
        """
        result = await self.db.execute(
            delete(ExportJob)
            .where(ExportJob.expires_at < before_date)
            .where(ExportJob.status == "completed")
        )
        await self.db.flush()
        return result.rowcount
