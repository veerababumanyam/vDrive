"""Cleanup task for expired uploads and orphaned files."""

import asyncio
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select

from ..core.database import async_session_factory
from ..models import Upload, UploadStatus
from ..services.storage_service import get_storage_service

logger = structlog.get_logger()


async def cleanup_expired_uploads(expiry_hours: int = 24):
    """
    Clean up expired uploads that are older than expiry_hours.

    Args:
        expiry_hours: Number of hours before an upload expires (default: 24)
    """
    logger.info("Starting expired upload cleanup", expiry_hours=expiry_hours)

    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=expiry_hours)

    async with async_session_factory() as db:
        # Find expired uploads that are not completed
        result = await db.execute(
            select(Upload).where(
                Upload.created_at < cutoff_time,
                Upload.status.in_([
                    UploadStatus.CREATED.value,
                    UploadStatus.UPLOADING.value,
                    UploadStatus.ASSEMBLING.value,
                ]),
            )
        )
        expired_uploads = result.scalars().all()

        logger.info("Found expired uploads", count=len(expired_uploads))

        storage_service = get_storage_service()
        cleaned_count = 0

        for upload in expired_uploads:
            try:
                # Cancel multipart upload in R2 if it exists
                if upload.r2_multipart_upload_id:
                    try:
                        storage_service.abort_multipart_upload(
                            key=upload.storage_path,
                            upload_id=upload.r2_multipart_upload_id,
                        )
                        logger.debug(
                            "Aborted multipart upload",
                            upload_id=upload.id,
                            r2_upload_id=upload.r2_multipart_upload_id,
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to abort multipart upload",
                            upload_id=upload.id,
                            error=str(e),
                        )

                # Mark upload as cancelled in database
                upload.status = UploadStatus.CANCELLED.value
                upload.error_message = f"Upload expired after {expiry_hours} hours"
                
                cleaned_count += 1

            except Exception as e:
                logger.error(
                    "Failed to cleanup upload",
                    upload_id=upload.id,
                    error=str(e),
                )

        await db.commit()

    logger.info(
        "Expired upload cleanup completed",
        cleaned_count=cleaned_count,
        total_expired=len(expired_uploads),
    )

    return cleaned_count


if __name__ == "__main__":
    # Run cleanup when executed directly
    asyncio.run(cleanup_expired_uploads())
