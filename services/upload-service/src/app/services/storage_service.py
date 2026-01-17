"""Cloudflare R2 storage service."""

from typing import Optional
import boto3
import structlog
from ..core.config import settings

logger = structlog.get_logger()

MIN_PART_SIZE = 5 * 1024 * 1024  # 5MB R2 minimum
MAX_PARTS = 10000


class R2StorageService:
    """Cloudflare R2 storage operations."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.R2_BUCKET_NAME

    def generate_object_key(
        self, workspace_id: str, asset_id: str, variant: str = "original", ext: str = "bin"
    ) -> str:
        """Generate structured R2 object key."""
        return f"workspaces/{workspace_id}/assets/{asset_id}/{variant}.{ext}"

    def init_multipart_upload(
        self, key: str, workspace_id: str, mime_type: str = "application/octet-stream"
    ) -> str:
        """Initialize R2 multipart upload."""
        try:
            response = self.client.create_multipart_upload(
                Bucket=self.bucket,
                Key=key,
                ContentType=mime_type,
                ServerSideEncryption="AES256",
                Metadata={"workspace_id": workspace_id, "encrypted": "aes-256-gcm-client"},
            )
            logger.info("Multipart upload initialized", key=key, upload_id=response["UploadId"])
            return response["UploadId"]
        except Exception as e:
            logger.error("Failed to initialize multipart upload", key=key, error=str(e))
            raise

    def upload_part(
        self, key: str, upload_id: str, part_number: int, data: bytes
    ) -> str:
        """Upload a part (min 5MB except last part)."""
        if len(data) < MIN_PART_SIZE and part_number < MAX_PARTS:
            logger.warning("Part size below minimum", size=len(data), min_size=MIN_PART_SIZE)

        try:
            response = self.client.upload_part(
                Bucket=self.bucket,
                Key=key,
                UploadId=upload_id,
                PartNumber=part_number,
                Body=data,
            )
            etag = response["ETag"]
            logger.debug("Part uploaded", part_number=part_number, etag=etag)
            return etag
        except Exception as e:
            logger.error("Failed to upload part", part_number=part_number, error=str(e))
            raise

    def complete_multipart_upload(
        self, key: str, upload_id: str, parts: list[dict]
    ) -> str:
        """Complete multipart upload."""
        try:
            response = self.client.complete_multipart_upload(
                Bucket=self.bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
            logger.info("Multipart upload completed", key=key, etag=response["ETag"])
            return response["ETag"]
        except Exception as e:
            logger.error("Failed to complete multipart upload", key=key, error=str(e))
            raise

    def abort_multipart_upload(self, key: str, upload_id: str):
        """Abort multipart upload (cleanup)."""
        try:
            self.client.abort_multipart_upload(
                Bucket=self.bucket, Key=key, UploadId=upload_id
            )
            logger.info("Multipart upload aborted", key=key, upload_id=upload_id)
        except Exception as e:
            logger.error("Failed to abort multipart upload", key=key, error=str(e))

    def generate_presigned_url(self, key: str, expiry: int = 3600) -> str:
        """Generate presigned URL for download."""
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expiry,
            )
            return url
        except Exception as e:
            logger.error("Failed to generate presigned URL", key=key, error=str(e))
            raise

    def delete_object(self, key: str):
        """Delete object from R2."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info("Object deleted", key=key)
        except Exception as e:
            logger.error("Failed to delete object", key=key, error=str(e))


# Singleton
_storage_service: Optional[R2StorageService] = None


def get_storage_service() -> R2StorageService:
    """Get storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = R2StorageService()
    return _storage_service
