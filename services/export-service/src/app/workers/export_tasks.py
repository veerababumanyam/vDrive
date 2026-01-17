"""
vDrive Export Service - Celery Tasks

Background tasks for processing export jobs, creating ZIP files, and uploading to R2.
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import httpx
from celery import Task
from zipstream import ZipStream

from src.app.core.config import settings
from src.app.core.database import async_session_maker
from src.app.repositories.export_repository import ExportRepository
from src.app.services.storage_service import StorageService
from src.app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


# ===========================================
# Helper Functions
# ===========================================


async def fetch_workspace_assets(
    workspace_id: str,
    export_options: dict,
) -> list[dict]:
    """
    Fetch all assets for a workspace export.

    Args:
        workspace_id: UUID of workspace
        export_options: Export options (gallery_ids, include_metadata, etc.)

    Returns:
        List of asset dictionaries with download URLs

    Raises:
        Exception: If fetching fails
    """
    try:
        # Determine which assets to fetch based on export_type
        gallery_ids = export_options.get("gallery_ids", [])

        # Call backend API to get assets
        async with httpx.AsyncClient(timeout=30.0) as client:
            if gallery_ids:
                # Fetch specific galleries
                params = {"gallery_ids": ",".join(gallery_ids)}
            else:
                # Fetch all workspace assets
                params = {"workspace_id": workspace_id}

            # Call backend/gallery service to get asset list
            # For now, we'll use a simplified approach
            # In production, this would call the actual backend API
            response = await client.get(
                f"{settings.GALLERY_SERVICE_URL}/api/v1/assets",
                params=params,
            )

            if response.status_code == 200:
                assets = response.json().get("assets", [])
                logger.info(
                    f"Fetched {len(assets)} assets for workspace {workspace_id}"
                )
                return assets
            else:
                logger.error(
                    f"Failed to fetch assets: {response.status_code} {response.text}"
                )
                return []

    except Exception as e:
        logger.error(f"Error fetching workspace assets: {e}")
        raise


async def create_export_zip(
    assets: list[dict],
    export_id: str,
    include_metadata: bool = True,
) -> str:
    """
    Create ZIP file from assets using zipstream-ng for memory efficiency.

    Args:
        assets: List of asset dictionaries with download URLs
        export_id: UUID of export job
        include_metadata: Whether to include metadata files

    Returns:
        Path to created ZIP file

    Raises:
        Exception: If ZIP creation fails
    """
    try:
        # Create temporary directory for ZIP creation
        temp_dir = Path(tempfile.gettempdir()) / "exports" / export_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        zip_path = temp_dir / f"export-{export_id}.zip"

        # Use ZipStream for memory-efficient ZIP creation
        zs = ZipStream(compress_type="deflate", compress_level=6)

        # Download and add each asset to ZIP
        async with httpx.AsyncClient(timeout=60.0) as client:
            for idx, asset in enumerate(assets):
                try:
                    # Get asset URL
                    asset_url = asset.get("url") or asset.get("download_url")
                    if not asset_url:
                        logger.warning(
                            f"Skipping asset {asset.get('id')} - no URL available"
                        )
                        continue

                    # Determine file path in ZIP (preserve gallery structure)
                    gallery_name = asset.get("gallery_name", "Uncategorized")
                    filename = asset.get("filename", f"asset-{asset['id']}")
                    zip_file_path = f"{gallery_name}/{filename}"

                    # Download asset
                    logger.debug(f"Downloading asset {idx + 1}/{len(assets)}: {filename}")
                    response = await client.get(asset_url)
                    response.raise_for_status()

                    # Add to ZIP stream
                    zs.add(response.content, arcname=zip_file_path)

                    # Add metadata if requested
                    if include_metadata and asset.get("metadata"):
                        metadata_path = f"{gallery_name}/.metadata/{filename}.json"
                        import json

                        metadata_json = json.dumps(asset["metadata"], indent=2)
                        zs.add(metadata_json.encode("utf-8"), arcname=metadata_path)

                except Exception as e:
                    logger.error(
                        f"Failed to add asset {asset.get('id')} to ZIP: {e}"
                    )
                    # Continue with other assets

        # Write ZIP stream to file
        with open(zip_path, "wb") as f:
            for chunk in zs:
                f.write(chunk)

        logger.info(f"Created ZIP file: {zip_path} ({zip_path.stat().st_size} bytes)")
        return str(zip_path)

    except Exception as e:
        logger.error(f"Error creating export ZIP: {e}")
        raise


async def process_export_job_async(export_id: str) -> None:
    """
    Async implementation of export job processing.

    Args:
        export_id: UUID of export job to process

    Raises:
        Exception: If processing fails
    """
    async with async_session_maker() as db:
        export_repo = ExportRepository(db)
        storage_service = StorageService()

        try:
            # 1. Get export job
            export_job = await export_repo.get_by_id(export_id)
            if not export_job:
                logger.error(f"Export job {export_id} not found")
                return

            logger.info(
                f"Processing export job {export_id}",
                extra={
                    "export_id": export_id,
                    "workspace_id": export_job.workspace_id,
                    "export_type": export_job.export_type,
                },
            )

            # 2. Update status to processing
            await export_repo.update_status(export_id, "processing")
            await db.commit()

            # 3. Fetch assets based on export type and options
            export_options = export_job.options or {}
            assets = await fetch_workspace_assets(
                workspace_id=export_job.workspace_id,
                export_options=export_options,
            )

            if not assets:
                logger.warning(f"No assets found for export {export_id}")
                await export_repo.mark_failed(
                    export_id=export_id,
                    error_message="No assets found to export",
                )
                await db.commit()
                return

            # 4. Update total assets count
            await export_repo.update(export_id, total_assets=len(assets))
            await db.commit()

            # 5. Create ZIP file with assets
            include_metadata = export_options.get("include_metadata", True)
            zip_path = await create_export_zip(
                assets=assets,
                export_id=export_id,
                include_metadata=include_metadata,
            )

            # 6. Update progress (all assets processed)
            await export_repo.update_progress(
                export_id=export_id,
                processed_assets=len(assets),
            )
            await db.commit()

            # 7. Upload to R2
            file_url, file_key = await storage_service.upload_export_file(
                file_path=zip_path,
                workspace_id=export_job.workspace_id,
                export_id=export_id,
                export_type=export_job.export_type,
                metadata={
                    "total_assets": len(assets),
                    "export_options": export_options,
                },
            )

            # 8. Get file size
            file_size = Path(zip_path).stat().st_size

            # 9. Calculate expiration
            expires_at = storage_service.calculate_expiration()

            # 10. Generate presigned download URL
            download_url = await storage_service.generate_download_url(file_key)
            if not download_url:
                download_url = file_url  # Fallback to public URL

            # 11. Mark job as completed
            await export_repo.mark_completed(
                export_id=export_id,
                file_url=download_url,
                file_size=file_size,
                file_key=file_key,
                expires_at=expires_at,
            )
            await db.commit()

            # 12. Clean up temporary files
            try:
                Path(zip_path).unlink()
                Path(zip_path).parent.rmdir()
            except Exception as e:
                logger.warning(f"Failed to clean up temp files: {e}")

            logger.info(
                f"Completed export job {export_id}",
                extra={
                    "export_id": export_id,
                    "file_size": file_size,
                    "total_assets": len(assets),
                },
            )

        except Exception as e:
            logger.error(
                f"Export job {export_id} failed: {e}",
                exc_info=True,
                extra={"export_id": export_id},
            )

            # Mark job as failed
            try:
                await export_repo.mark_failed(
                    export_id=export_id,
                    error_message=str(e),
                )
                await db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update job status: {update_error}")

            raise


# ===========================================
# Celery Tasks
# ===========================================


@celery_app.task(
    bind=True,
    name="src.app.workers.export_tasks.process_export_job",
    max_retries=3,
    soft_time_limit=6900,  # 1 hour 55 minutes
    time_limit=7200,  # 2 hours
)
def process_export_job(self: Task, export_id: str) -> dict:
    """
    Process export job - main Celery task.

    Fetches assets, creates ZIP file, uploads to R2, and updates job status.

    Args:
        export_id: UUID of export job to process

    Returns:
        Dict with task result information
    """
    try:
        # Run async function in event loop
        asyncio.run(process_export_job_async(export_id))

        return {
            "status": "completed",
            "export_id": export_id,
            "message": "Export job processed successfully",
        }

    except Exception as e:
        logger.error(f"Export job {export_id} failed: {e}")

        # Retry on failure (with exponential backoff)
        try:
            self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error(
                f"Export job {export_id} failed after {self.max_retries} retries"
            )
            return {
                "status": "failed",
                "export_id": export_id,
                "error": str(e),
            }


@celery_app.task(
    bind=True,
    name="src.app.workers.export_tasks.cleanup_expired_exports",
)
def cleanup_expired_exports(self: Task) -> dict:
    """
    Clean up expired export jobs - scheduled Celery task.

    Runs periodically (configured in celery_app.py beat_schedule).
    Deletes export files from R2 and removes database records.

    Returns:
        Dict with cleanup statistics
    """

    async def cleanup_async():
        async with async_session_maker() as db:
            export_repo = ExportRepository(db)
            storage_service = StorageService()

            try:
                now = datetime.now(timezone.utc)

                # 1. Find expired export jobs
                expired_jobs = []
                # Query completed jobs with expires_at in the past
                all_jobs = await export_repo.list_by_workspace(
                    workspace_id="",  # Will need to iterate all workspaces
                    limit=1000,
                    offset=0,
                    status_filter="completed",
                )

                for job in all_jobs:
                    if job.expires_at and job.expires_at < now:
                        expired_jobs.append(job)

                logger.info(f"Found {len(expired_jobs)} expired export jobs")

                # 2. Delete files from R2
                deleted_files = 0
                for job in expired_jobs:
                    if job.file_key:
                        success = await storage_service.delete_export_file(
                            object_key=job.file_key,
                            export_id=job.id,
                        )
                        if success:
                            deleted_files += 1

                # 3. Delete database records
                deleted_records = await export_repo.delete_expired(before_date=now)
                await db.commit()

                logger.info(
                    f"Cleanup completed: {deleted_files} files, {deleted_records} records"
                )

                return {
                    "deleted_files": deleted_files,
                    "deleted_records": deleted_records,
                }

            except Exception as e:
                logger.error(f"Cleanup task failed: {e}", exc_info=True)
                raise

    try:
        result = asyncio.run(cleanup_async())
        return {
            "status": "completed",
            "deleted_files": result["deleted_files"],
            "deleted_records": result["deleted_records"],
        }

    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
        }
