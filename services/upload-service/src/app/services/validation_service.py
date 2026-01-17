"""Upload validation and limiting service."""

import hashlib
from typing import Optional

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models import Upload, UploadStatus

logger = structlog.get_logger()

# MIME types allowed for upload (from spec.md FR-003)
ALLOWED_MIME_TYPES = [
    # Images - JPEG
    "image/jpeg",
    "image/jpg",
    # Images - PNG
    "image/png",
    # Images - WebP
    "image/webp",
    # Images - HEIC
    "image/heic",
    "image/heif",
    # RAW formats
    "image/x-canon-cr2",
    "image/x-canon-cr3",
    "image/x-nikon-nef",
    "image/x-sony-arw",
    "image/x-adobe-dng",
    "image/x-fuji-raf",
    "image/x-olympus-orf",
    "image/x-panasonic-rw2",
    # Videos
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska",
]


class ValidationService:
    """Upload validation and rate limiting."""

    @staticmethod
    def validate_mime_type(mime_type: str) -> bool:
        """
        Check if MIME type is allowed.

        Args:
            mime_type: MIME type string (e.g., "image/jpeg")

        Returns:
            True if allowed, False otherwise
        """
        return mime_type.lower() in ALLOWED_MIME_TYPES

    @staticmethod
    def validate_file_size(size: int) -> bool:
        """
        Check if file size is within limits.

        Args:
            size: File size in bytes

        Returns:
            True if within limits, False otherwise
        """
        if size <= 0:
            return False
        if size > settings.TUS_MAX_SIZE:
            return False
        return True

    @staticmethod
    async def check_concurrent_uploads(
        workspace_id: str, db: AsyncSession
    ) -> tuple[bool, int]:
        """
        Check if workspace has reached concurrent upload limit.

        Args:
            workspace_id: Workspace ID
            db: Database session

        Returns:
            Tuple of (is_allowed, current_count)
        """
        try:
            # Count active uploads for workspace
            result = await db.execute(
                select(func.count(Upload.id)).where(
                    Upload.workspace_id == workspace_id,
                    Upload.status.in_([
                        UploadStatus.CREATED.value,
                        UploadStatus.UPLOADING.value,
                        UploadStatus.ASSEMBLING.value,
                    ]),
                )
            )
            count = result.scalar() or 0

            is_allowed = count < settings.MAX_CONCURRENT_UPLOADS_PER_WORKSPACE

            logger.debug(
                "Concurrent upload check",
                workspace_id=workspace_id,
                current_count=count,
                limit=settings.MAX_CONCURRENT_UPLOADS_PER_WORKSPACE,
                is_allowed=is_allowed,
            )

            return is_allowed, count

        except Exception as e:
            logger.error(
                "Failed to check concurrent uploads",
                workspace_id=workspace_id,
                error=str(e),
            )
            # Fail open to avoid blocking uploads
            return True, 0

    @staticmethod
    def validate_checksum_sha256(data: bytes, expected_checksum: str) -> bool:
        """
        Validate SHA-256 checksum.

        Args:
            data: Data bytes
            expected_checksum: Expected SHA-256 hex string

        Returns:
            True if checksum matches, False otherwise
        """
        if not expected_checksum:
            # No checksum provided, skip validation
            return True

        calculated = hashlib.sha256(data).hexdigest()
        return calculated.lower() == expected_checksum.lower()

    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Validate filename for security.

        Args:
            filename: Original filename

        Returns:
            True if safe, False otherwise
        """
        if not filename or len(filename) > 255:
            return False

        # Reject path traversal attempts
        if "../" in filename or "..\\" in filename:
            return False
        if filename.startswith("/") or filename.startswith("\\"):
            return False

        # Reject hidden files
        if filename.startswith("."):
            return False

        return True


# Singleton instance
_validation_service: Optional[ValidationService] = None


def get_validation_service() -> ValidationService:
    """Get validation service instance."""
    global _validation_service
    if _validation_service is None:
        _validation_service = ValidationService()
    return _validation_service
