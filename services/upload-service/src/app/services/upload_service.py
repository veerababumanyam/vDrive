"""Upload orchestration service."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from ..core.config import settings
from ..models import Upload, Asset, UploadStatus, ProcessingStatus
from ..schemas.events import UploadInitiatedEvent, UploadCompletedEvent
from .encryption_service import get_encryption_service
from .storage_service import get_storage_service
from .event_service import get_event_service

logger = structlog.get_logger()


class UploadService:
    """Upload lifecycle orchestration."""

    @staticmethod
    async def create_upload_session(
        workspace_id: str,
        user_id: str,
        filename: str,
        mime_type: str,
        expected_size: int,
        checksum_client: Optional[str],
        db: AsyncSession,
    ) -> Upload:
        """Create TUS upload session."""
        upload_id = str(uuid4())
        upload_url = f"{settings.API_BASE_URL}/api/v1/files/{upload_id}"
        expires_at = datetime.utcnow() + timedelta(hours=settings.TUS_UPLOAD_URL_TTL_HOURS)

        upload = Upload(
            id=upload_id,
            workspace_id=workspace_id,
            user_id=user_id,
            filename=filename,
            mime_type=mime_type,
            expected_size=expected_size,
            checksum_client=checksum_client,
            upload_url=upload_url,
            expires_at=expires_at,
            status=UploadStatus.CREATED.value,
        )

        db.add(upload)
        await db.commit()
        await db.refresh(upload)

        # Publish upload.initiated event
        event = UploadInitiatedEvent(
            upload_id=upload.id,
            workspace_id=workspace_id,
            filename=filename,
            expected_size=expected_size,
        )
        await get_event_service().publish_event("upload.initiated", event, workspace_id)

        logger.info("Upload session created", upload_id=upload_id, filename=filename)
        return upload

    @staticmethod
    async def complete_upload(
        upload: Upload,
        checksum_server: str,
        storage_path: str,
        db: AsyncSession,
    ) -> Asset:
        """Complete upload and create Asset."""
        # Validate checksum
        if upload.checksum_client and upload.checksum_client != checksum_server:
            raise ValueError("Checksum mismatch")

        # Create Asset
        asset_id = str(uuid4())
        encryption_service = get_encryption_service()
        
        # Derive encryption key
        workspace_key = encryption_service.derive_workspace_key(upload.workspace_id)
        encryption_metadata = encryption_service.generate_encryption_metadata()

        asset = Asset(
            id=asset_id,
            workspace_id=upload.workspace_id,
            upload_id=upload.id,
            original_key=storage_path,
            mime_type=upload.mime_type,
            file_size=upload.expected_size,
            is_encrypted=True,
            encryption_key_id=f"ws-{upload.workspace_id}-v1",
            encryption_iv=bytes.fromhex(encryption_metadata["iv"]),
            checksum=checksum_server,
            processing_status=ProcessingStatus.PENDING.value,
        )

        db.add(asset)
        upload.status = UploadStatus.COMPLETED.value
        upload.checksum_server = checksum_server
        await db.commit()

        # Publish upload.completed event
        event = UploadCompletedEvent(
            upload_id=upload.id,
            workspace_id=upload.workspace_id,
            asset_id=asset.id,
            filename=upload.filename,
            mime_type=upload.mime_type,
            file_size=upload.expected_size,
            storage_path=storage_path,
            checksum=checksum_server,
            is_encrypted=True,
            encryption_key_id=asset.encryption_key_id,
        )
        await get_event_service().publish_event("upload.completed", event, upload.workspace_id)

        logger.info("Upload completed", upload_id=upload.id, asset_id=asset.id)
        return asset


def get_upload_service() -> UploadService:
    """Get upload service instance."""
    return UploadService()
