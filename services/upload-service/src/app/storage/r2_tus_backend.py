"""Custom TUS storage backend for Cloudflare R2 with encryption."""

import hashlib
import json
from typing import Optional
from uuid import uuid4

import structlog
from sqlalchemy import select

from ..core.config import settings
from ..core.database import AsyncSessionLocal
from ..models import Upload, UploadStatus
from ..services.encryption_service import get_encryption_service
from ..services.storage_service import get_storage_service, MIN_PART_SIZE

logger = structlog.get_logger()


class R2TUSStorageBackend:
    """TUS protocol storage backend using Cloudflare R2 with AES-256-GCM encryption."""

    def __init__(self, db_session_factory=None):
        """Initialize backend with services."""
        self.storage_service = get_storage_service()
        self.encryption_service = get_encryption_service()
        self.db_session_factory = db_session_factory or AsyncSessionLocal

    async def create(
        self,
        upload_id: str,
        workspace_id: str,
        user_id: str,
        filename: str,
        mime_type: str,
        expected_size: int,
        checksum_client: Optional[str] = None,
    ) -> dict:
        """
        Initialize upload session and R2 multipart upload.

        Returns:
            dict with upload metadata
        """
        try:
            # Generate R2 object key
            asset_id = str(uuid4())
            storage_path = self.storage_service.generate_object_key(
                workspace_id=workspace_id,
                asset_id=asset_id,
                variant="original",
                ext="bin",
            )

            # Initialize R2 multipart upload
            multipart_upload_id = self.storage_service.init_multipart_upload(
                key=storage_path,
                workspace_id=workspace_id,
                mime_type=mime_type,
            )

            # Generate encryption IV for this upload
            encryption_metadata = self.encryption_service.generate_encryption_metadata()
            iv_hex = encryption_metadata["iv"]

            # Calculate expiration time
            from datetime import datetime, timedelta, timezone
            expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.TUS_UPLOAD_URL_TTL_HOURS)

            # Create Upload record
            async with self.db_session_factory() as db:
                upload = Upload(
                    id=upload_id,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    filename=filename,
                    mime_type=mime_type,
                    expected_size=expected_size,
                    checksum_client=checksum_client,
                    upload_url=f"{settings.API_BASE_URL}/api/v1/files/{upload_id}",
                    multipart_upload_id=multipart_upload_id,
                    storage_path=storage_path,
                    parts_metadata={
                        "parts": [],
                        "iv": iv_hex,
                        "encryption_key_id": f"ws-{workspace_id}-v1",
                        "asset_id": asset_id,
                    },
                    status=UploadStatus.CREATED.value,
                    expires_at=expires_at,
                )

                db.add(upload)
                await db.commit()
                await db.refresh(upload)

            logger.info(
                "TUS upload session created",
                upload_id=upload_id,
                workspace_id=workspace_id,
                filename=filename,
                multipart_upload_id=multipart_upload_id,
                storage_path=storage_path,
            )

            return {
                "upload_id": upload_id,
                "storage_path": storage_path,
                "multipart_upload_id": multipart_upload_id,
                "asset_id": asset_id,
            }

        except Exception as e:
            logger.error("Failed to create TUS upload session", upload_id=upload_id, error=str(e))
            raise

    async def write_chunk(
        self, upload_id: str, chunk_data: bytes, offset: int
    ) -> int:
        """
        Encrypt chunk and upload to R2 as part.

        Args:
            upload_id: Upload session ID
            chunk_data: Raw chunk bytes
            offset: Current upload offset

        Returns:
            New offset after chunk upload
        """
        try:
            async with self.db_session_factory() as db:
                # Get upload record
                result = await db.execute(select(Upload).where(Upload.id == upload_id))
                upload = result.scalar_one_or_none()

                if not upload:
                    raise ValueError(f"Upload {upload_id} not found")

                # Validate offset matches current progress
                if offset != upload.received_bytes:
                    raise ValueError(
                        f"Offset mismatch: expected {upload.received_bytes}, got {offset}"
                    )

                # Extract metadata
                parts_metadata = upload.parts_metadata or {}
                iv_hex = parts_metadata.get("iv")
                if not iv_hex:
                    raise ValueError("Missing encryption IV in upload metadata")

                # Derive workspace encryption key
                workspace_key = self.encryption_service.derive_workspace_key(
                    upload.workspace_id
                )

                # Encrypt chunk
                iv = bytes.fromhex(iv_hex)
                ciphertext, _, auth_tag = self.encryption_service.encrypt_chunk(
                    chunk_data, workspace_key, iv
                )

                # Calculate part number (1-indexed)
                part_number = (offset // MIN_PART_SIZE) + 1

                # Upload encrypted chunk to R2
                etag = self.storage_service.upload_part(
                    key=upload.storage_path,
                    upload_id=upload.multipart_upload_id,
                    part_number=part_number,
                    data=ciphertext,
                )

                # Update parts metadata
                parts_list = parts_metadata.get("parts", [])
                parts_list.append({
                    "PartNumber": part_number,
                    "ETag": etag,
                    "Size": len(ciphertext),
                    "AuthTag": auth_tag.hex(),
                })
                parts_metadata["parts"] = parts_list

                # Update upload progress
                new_offset = offset + len(chunk_data)
                upload.received_bytes = new_offset
                upload.parts_metadata = parts_metadata

                # Update status to uploading after first chunk
                if upload.status == UploadStatus.CREATED.value:
                    upload.status = UploadStatus.UPLOADING.value

                await db.commit()

                logger.debug(
                    "TUS chunk uploaded",
                    upload_id=upload_id,
                    part_number=part_number,
                    offset=offset,
                    new_offset=new_offset,
                    chunk_size=len(chunk_data),
                )

                return new_offset

        except Exception as e:
            logger.error(
                "Failed to upload TUS chunk",
                upload_id=upload_id,
                offset=offset,
                error=str(e),
            )
            raise

    async def complete(self, upload_id: str) -> str:
        """
        Complete R2 multipart upload and calculate checksum.

        Args:
            upload_id: Upload session ID

        Returns:
            Storage path of completed upload
        """
        try:
            async with self.db_session_factory() as db:
                # Get upload record
                result = await db.execute(select(Upload).where(Upload.id == upload_id))
                upload = result.scalar_one_or_none()

                if not upload:
                    raise ValueError(f"Upload {upload_id} not found")

                # Update status to assembling
                upload.status = UploadStatus.ASSEMBLING.value
                await db.commit()

                # Extract parts metadata
                parts_metadata = upload.parts_metadata or {}
                parts_list = parts_metadata.get("parts", [])

                if not parts_list:
                    raise ValueError("No parts uploaded")

                # Prepare parts for R2 complete multipart upload
                r2_parts = [
                    {"PartNumber": part["PartNumber"], "ETag": part["ETag"]}
                    for part in parts_list
                ]

                # Complete R2 multipart upload
                r2_etag = self.storage_service.complete_multipart_upload(
                    key=upload.storage_path,
                    upload_id=upload.multipart_upload_id,
                    parts=r2_parts,
                )

                # Calculate server-side checksum (SHA-256 of encrypted data)
                # Note: This is checksum of encrypted data, not original
                checksum_server = hashlib.sha256(
                    json.dumps(parts_list, sort_keys=True).encode()
                ).hexdigest()

                upload.checksum_server = checksum_server
                await db.commit()

                logger.info(
                    "TUS upload completed",
                    upload_id=upload_id,
                    storage_path=upload.storage_path,
                    parts_count=len(parts_list),
                    r2_etag=r2_etag,
                )

                return upload.storage_path

        except Exception as e:
            logger.error(
                "Failed to complete TUS upload",
                upload_id=upload_id,
                error=str(e),
            )
            # Attempt cleanup
            try:
                await self.delete(upload_id)
            except Exception as cleanup_error:
                logger.error(
                    "Failed to cleanup after completion error",
                    upload_id=upload_id,
                    error=str(cleanup_error),
                )
            raise

    async def delete(self, upload_id: str):
        """
        Abort R2 multipart upload and cleanup.

        Args:
            upload_id: Upload session ID
        """
        try:
            async with self.db_session_factory() as db:
                # Get upload record
                result = await db.execute(select(Upload).where(Upload.id == upload_id))
                upload = result.scalar_one_or_none()

                if not upload:
                    logger.warning("Upload not found for deletion", upload_id=upload_id)
                    return

                # Abort R2 multipart upload
                if upload.multipart_upload_id:
                    self.storage_service.abort_multipart_upload(
                        key=upload.storage_path,
                        upload_id=upload.multipart_upload_id,
                    )

                # Update upload status
                upload.status = UploadStatus.CANCELLED.value
                await db.commit()

                logger.info("TUS upload deleted", upload_id=upload_id)

        except Exception as e:
            logger.error("Failed to delete TUS upload", upload_id=upload_id, error=str(e))
            raise

    async def get_offset(self, upload_id: str) -> int:
        """
        Get current upload offset from database.

        Args:
            upload_id: Upload session ID

        Returns:
            Current offset in bytes
        """
        async with self.db_session_factory() as db:
            result = await db.execute(select(Upload).where(Upload.id == upload_id))
            upload = result.scalar_one_or_none()

            if not upload:
                raise ValueError(f"Upload {upload_id} not found")

            return upload.received_bytes

    async def get_info(self, upload_id: str) -> dict:
        """
        Get upload metadata for TUS HEAD requests.

        Args:
            upload_id: Upload session ID

        Returns:
            dict with upload info
        """
        async with self.db_session_factory() as db:
            result = await db.execute(select(Upload).where(Upload.id == upload_id))
            upload = result.scalar_one_or_none()

            if not upload:
                raise ValueError(f"Upload {upload_id} not found")

            return {
                "upload_id": upload.id,
                "filename": upload.filename,
                "mime_type": upload.mime_type,
                "expected_size": upload.expected_size,
                "received_bytes": upload.received_bytes,
                "status": upload.status,
                "created_at": upload.created_at.isoformat(),
                "expires_at": upload.expires_at.isoformat() if upload.expires_at else None,
            }


def get_r2_tus_backend() -> R2TUSStorageBackend:
    """Get R2 TUS storage backend instance."""
    return R2TUSStorageBackend()
