"""
Cloudflare R2 storage client for Export Service.

Provides S3-compatible storage operations for export files using boto3.
"""

import logging
from io import BytesIO
from typing import Optional

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from src.app.core.config import settings

logger = logging.getLogger(__name__)


class StorageClient:
    """
    Cloudflare R2 storage client using boto3 S3 API.

    R2 is S3-compatible, so we use boto3's S3 client with R2 endpoint.
    """

    def __init__(self):
        """Initialize R2 client with boto3."""
        self._client = None
        self._bucket_name = settings.R2_BUCKET_NAME

    def _get_client(self):
        """
        Get or create boto3 S3 client.

        Lazy initialization to avoid connection on import.
        """
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.R2_ENDPOINT_URL,
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                config=Config(
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "adaptive"},
                ),
            )
        return self._client

    async def upload_file(
        self,
        file_path: str,
        object_key: str,
        content_type: str = "application/zip",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload file to R2 storage.

        Args:
            file_path: Local file path to upload
            object_key: S3 object key (path in bucket)
            content_type: MIME type of file
            metadata: Optional metadata to attach

        Returns:
            Public URL of uploaded file

        Raises:
            ClientError: If upload fails
        """
        try:
            client = self._get_client()

            extra_args = {
                "ContentType": content_type,
            }

            if metadata:
                extra_args["Metadata"] = metadata

            with open(file_path, "rb") as f:
                client.upload_fileobj(
                    f,
                    self._bucket_name,
                    object_key,
                    ExtraArgs=extra_args,
                )

            # Generate public URL
            public_url = f"{settings.R2_PUBLIC_URL}/{object_key}"
            logger.info(f"Uploaded file to R2: {object_key}")

            return public_url

        except ClientError as e:
            logger.error(f"Failed to upload file to R2: {e}")
            raise

    async def upload_fileobj(
        self,
        file_obj: BytesIO,
        object_key: str,
        content_type: str = "application/zip",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload file object to R2 storage.

        Args:
            file_obj: File-like object to upload
            object_key: S3 object key (path in bucket)
            content_type: MIME type of file
            metadata: Optional metadata to attach

        Returns:
            Public URL of uploaded file

        Raises:
            ClientError: If upload fails
        """
        try:
            client = self._get_client()

            extra_args = {
                "ContentType": content_type,
            }

            if metadata:
                extra_args["Metadata"] = metadata

            client.upload_fileobj(
                file_obj,
                self._bucket_name,
                object_key,
                ExtraArgs=extra_args,
            )

            # Generate public URL
            public_url = f"{settings.R2_PUBLIC_URL}/{object_key}"
            logger.info(f"Uploaded file object to R2: {object_key}")

            return public_url

        except ClientError as e:
            logger.error(f"Failed to upload file object to R2: {e}")
            raise

    async def delete_file(self, object_key: str) -> bool:
        """
        Delete file from R2 storage.

        Args:
            object_key: S3 object key (path in bucket)

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            client = self._get_client()
            client.delete_object(Bucket=self._bucket_name, Key=object_key)
            logger.info(f"Deleted file from R2: {object_key}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete file from R2: {e}")
            return False

    async def generate_presigned_url(
        self,
        object_key: str,
        expiration: int = 3600,
    ) -> Optional[str]:
        """
        Generate presigned URL for temporary access to file.

        Args:
            object_key: S3 object key (path in bucket)
            expiration: URL expiration in seconds (default 1 hour)

        Returns:
            Presigned URL or None if failed
        """
        try:
            client = self._get_client()
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket_name, "Key": object_key},
                ExpiresIn=expiration,
            )
            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

    async def check_connection(self) -> bool:
        """
        Health check for R2 storage connectivity.

        Returns:
            True if R2 is reachable, False otherwise
        """
        try:
            client = self._get_client()
            client.head_bucket(Bucket=self._bucket_name)
            return True

        except ClientError:
            return False


# Global storage client instance
storage_client = StorageClient()
