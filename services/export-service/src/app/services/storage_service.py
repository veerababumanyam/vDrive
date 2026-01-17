"""
Storage service for export file operations.

Provides high-level R2 storage operations for export files.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from src.app.core.config import settings
from src.app.core.storage import storage_client

logger = logging.getLogger(__name__)


class StorageService:
    """
    Service for managing export file storage on R2.

    Wraps StorageClient with export-specific business logic.
    """

    def __init__(self):
        """Initialize storage service."""
        self.storage_client = storage_client

    def generate_export_key(
        self,
        workspace_id: str,
        export_id: str,
        export_type: str,
    ) -> str:
        """
        Generate unique R2 object key for export file.

        Args:
            workspace_id: UUID of workspace
            export_id: UUID of export job
            export_type: Type of export (workspace, gallery, selection)

        Returns:
            R2 object key (e.g., "exports/workspace-123/export-456.zip")
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        filename = f"{export_type}-{export_id}-{timestamp}.zip"
        key = f"exports/{workspace_id}/{filename}"
        return key

    async def upload_export_file(
        self,
        file_path: str,
        workspace_id: str,
        export_id: str,
        export_type: str,
        metadata: Optional[dict] = None,
    ) -> tuple[str, str]:
        """
        Upload export file to R2 storage.

        Args:
            file_path: Local path to export file
            workspace_id: UUID of workspace
            export_id: UUID of export job
            export_type: Type of export
            metadata: Optional metadata to attach

        Returns:
            Tuple of (public_url, object_key)

        Raises:
            Exception: If upload fails
        """
        try:
            object_key = self.generate_export_key(
                workspace_id=workspace_id,
                export_id=export_id,
                export_type=export_type,
            )

            # Add export metadata
            export_metadata = {
                "workspace_id": workspace_id,
                "export_id": export_id,
                "export_type": export_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if metadata:
                export_metadata.update(metadata)

            public_url = await self.storage_client.upload_file(
                file_path=file_path,
                object_key=object_key,
                content_type="application/zip",
                metadata=export_metadata,
            )

            logger.info(
                f"Uploaded export file: {object_key}",
                extra={
                    "export_id": export_id,
                    "workspace_id": workspace_id,
                    "file_size": Path(file_path).stat().st_size,
                },
            )

            return public_url, object_key

        except Exception as e:
            logger.error(
                f"Failed to upload export file: {e}",
                extra={
                    "export_id": export_id,
                    "workspace_id": workspace_id,
                },
            )
            raise

    async def generate_download_url(
        self,
        object_key: str,
        expiration_hours: Optional[int] = None,
    ) -> Optional[str]:
        """
        Generate presigned download URL for export file.

        Args:
            object_key: R2 object key
            expiration_hours: URL expiration in hours (default: EXPORT_RETENTION_HOURS)

        Returns:
            Presigned URL or None if failed
        """
        if expiration_hours is None:
            expiration_hours = settings.EXPORT_RETENTION_HOURS

        expiration_seconds = expiration_hours * 3600

        try:
            url = await self.storage_client.generate_presigned_url(
                object_key=object_key,
                expiration=expiration_seconds,
            )

            if url:
                logger.info(
                    f"Generated download URL for {object_key} (expires in {expiration_hours}h)"
                )

            return url

        except Exception as e:
            logger.error(f"Failed to generate download URL: {e}")
            return None

    async def delete_export_file(
        self,
        object_key: str,
        export_id: Optional[str] = None,
    ) -> bool:
        """
        Delete export file from R2 storage.

        Args:
            object_key: R2 object key
            export_id: Optional export ID for logging

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            success = await self.storage_client.delete_file(object_key)

            if success:
                logger.info(
                    f"Deleted export file: {object_key}",
                    extra={"export_id": export_id} if export_id else {},
                )
            else:
                logger.warning(
                    f"Failed to delete export file: {object_key}",
                    extra={"export_id": export_id} if export_id else {},
                )

            return success

        except Exception as e:
            logger.error(
                f"Error deleting export file: {e}",
                extra={"export_id": export_id} if export_id else {},
            )
            return False

    async def cleanup_expired_exports(
        self,
        export_jobs: list,
    ) -> int:
        """
        Delete export files for expired jobs.

        Args:
            export_jobs: List of ExportJob instances with expired files

        Returns:
            Number of files successfully deleted
        """
        deleted_count = 0

        for job in export_jobs:
            if job.file_key:
                success = await self.delete_export_file(
                    object_key=job.file_key,
                    export_id=job.id,
                )
                if success:
                    deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} expired export files")
        return deleted_count

    def calculate_expiration(
        self,
        retention_hours: Optional[int] = None,
    ) -> datetime:
        """
        Calculate expiration datetime for export file.

        Args:
            retention_hours: Retention period in hours (default: EXPORT_RETENTION_HOURS)

        Returns:
            Expiration datetime
        """
        if retention_hours is None:
            retention_hours = settings.EXPORT_RETENTION_HOURS

        return datetime.now(timezone.utc) + timedelta(hours=retention_hours)

    async def check_storage_health(self) -> bool:
        """
        Check if R2 storage is accessible.

        Returns:
            True if storage is healthy, False otherwise
        """
        try:
            return await self.storage_client.check_connection()
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return False
