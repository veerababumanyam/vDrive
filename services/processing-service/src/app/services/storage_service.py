"""Storage service for downloading from R2."""

import boto3
import structlog

from ..core.config import settings

logger = structlog.get_logger()


class R2StorageService:
    """Download files from Cloudflare R2."""

    def __init__(self):
        """Initialize R2 storage service."""
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.R2_BUCKET_NAME

    def download_object(self, key: str) -> bytes:
        """
        Download object from R2.

        Args:
            key: R2 object key

        Returns:
            Object bytes
        """
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            data = response["Body"].read()

            logger.debug("Downloaded from R2", key=key, size=len(data))

            return data

        except Exception as e:
            logger.error("Failed to download from R2", key=key, error=str(e))
            raise

    def upload_object(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict = None,
    ) -> str:
        """
        Upload object to R2.

        Args:
            key: R2 object key
            data: Object bytes
            content_type: MIME type
            metadata: Optional metadata dict

        Returns:
            Object ETag
        """
        try:
            response = self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                ServerSideEncryption="AES256",
                Metadata=metadata or {},
            )

            etag = response["ETag"]

            logger.debug("Uploaded to R2", key=key, size=len(data), etag=etag)

            return etag

        except Exception as e:
            logger.error("Failed to upload to R2", key=key, error=str(e))
            raise


# Singleton instance
_storage_service = None


def get_storage_service() -> R2StorageService:
    """Get storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = R2StorageService()
    return _storage_service
