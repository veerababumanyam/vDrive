"""
Storage service for Cloudflare R2 interactions using boto3.

Handles image upload, download, deletion, and URL generation for R2 storage.
"""

import asyncio
import io
import logging
from typing import BinaryIO, Optional
from urllib.parse import urljoin

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.app.core.config import settings

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage operations."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class StorageService:
    """
    Service for Cloudflare R2 storage operations.

    Uses boto3 S3 client with R2-compatible endpoint. All operations
    are thread-safe and can be used in async contexts.
    """

    def __init__(self):
        """
        Initialize R2 storage service with boto3 client.

        Raises:
            StorageError: If R2 credentials are not configured
        """
        if not settings.R2_ACCESS_KEY_ID or not settings.R2_SECRET_ACCESS_KEY:
            raise StorageError("R2 credentials not configured")

        if not settings.R2_ENDPOINT:
            raise StorageError("R2 endpoint not configured")

        # Configure boto3 client for R2
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(
                signature_version="s3v4",
                retries={
                    "max_attempts": 3,
                    "mode": "adaptive",
                },
            ),
        )
        self.bucket_name = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL

    async def upload_file(
        self,
        file_data: bytes,
        key: str,
        content_type: str = "image/jpeg",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload a file to R2 storage.

        Args:
            file_data: Binary file data to upload
            key: S3 object key (path in bucket)
            content_type: MIME type of the file
            metadata: Optional metadata dict to attach to object

        Returns:
            Public URL of uploaded file

        Raises:
            StorageError: If upload fails
        """
        try:
            # Run S3 upload in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_data,
                    ContentType=content_type,
                    Metadata=metadata or {},
                ),
            )

            logger.info(f"Uploaded file to R2: {key}")
            return self.get_public_url(key)

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to upload file to R2: {key}, error: {e}")
            raise StorageError(f"Failed to upload file: {key}", original_error=e)

    async def upload_fileobj(
        self,
        file_obj: BinaryIO,
        key: str,
        content_type: str = "image/jpeg",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload a file object to R2 storage.

        Args:
            file_obj: File-like object with read() method
            key: S3 object key (path in bucket)
            content_type: MIME type of the file
            metadata: Optional metadata dict to attach to object

        Returns:
            Public URL of uploaded file

        Raises:
            StorageError: If upload fails
        """
        try:
            # Run S3 upload in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    key,
                    ExtraArgs={
                        "ContentType": content_type,
                        "Metadata": metadata or {},
                    },
                ),
            )

            logger.info(f"Uploaded file object to R2: {key}")
            return self.get_public_url(key)

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to upload file object to R2: {key}, error: {e}")
            raise StorageError(f"Failed to upload file: {key}", original_error=e)

    async def download_file(self, key: str) -> bytes:
        """
        Download a file from R2 storage.

        Args:
            key: S3 object key (path in bucket)

        Returns:
            File data as bytes

        Raises:
            StorageError: If download fails or file not found
        """
        try:
            # Run S3 download in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=key,
                ),
            )

            # Read body content
            file_data = response["Body"].read()
            logger.info(f"Downloaded file from R2: {key}")
            return file_data

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.warning(f"File not found in R2: {key}")
                raise StorageError(f"File not found: {key}", original_error=e)
            logger.error(f"Failed to download file from R2: {key}, error: {e}")
            raise StorageError(f"Failed to download file: {key}", original_error=e)
        except BotoCoreError as e:
            logger.error(f"Failed to download file from R2: {key}, error: {e}")
            raise StorageError(f"Failed to download file: {key}", original_error=e)

    async def download_fileobj(self, key: str, file_obj: BinaryIO) -> None:
        """
        Download a file from R2 storage to a file object.

        Args:
            key: S3 object key (path in bucket)
            file_obj: File-like object with write() method

        Raises:
            StorageError: If download fails or file not found
        """
        try:
            # Run S3 download in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.download_fileobj(
                    self.bucket_name,
                    key,
                    file_obj,
                ),
            )

            logger.info(f"Downloaded file object from R2: {key}")

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.warning(f"File not found in R2: {key}")
                raise StorageError(f"File not found: {key}", original_error=e)
            logger.error(f"Failed to download file object from R2: {key}, error: {e}")
            raise StorageError(f"Failed to download file: {key}", original_error=e)
        except BotoCoreError as e:
            logger.error(f"Failed to download file object from R2: {key}, error: {e}")
            raise StorageError(f"Failed to download file: {key}", original_error=e)

    async def delete_file(self, key: str) -> None:
        """
        Delete a file from R2 storage.

        Args:
            key: S3 object key (path in bucket)

        Raises:
            StorageError: If deletion fails
        """
        try:
            # Run S3 delete in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=key,
                ),
            )

            logger.info(f"Deleted file from R2: {key}")

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to delete file from R2: {key}, error: {e}")
            raise StorageError(f"Failed to delete file: {key}", original_error=e)

    async def delete_files(self, keys: list[str]) -> None:
        """
        Delete multiple files from R2 storage in batch.

        Args:
            keys: List of S3 object keys to delete

        Raises:
            StorageError: If deletion fails
        """
        if not keys:
            return

        try:
            # Run S3 batch delete in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={
                        "Objects": [{"Key": key} for key in keys],
                        "Quiet": True,
                    },
                ),
            )

            logger.info(f"Deleted {len(keys)} files from R2")

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to delete files from R2: {e}")
            raise StorageError(f"Failed to delete {len(keys)} files", original_error=e)

    async def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in R2 storage.

        Args:
            key: S3 object key (path in bucket)

        Returns:
            True if file exists, False otherwise
        """
        try:
            # Run S3 head_object in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=key,
                ),
            )
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.error(f"Failed to check file existence in R2: {key}, error: {e}")
            raise StorageError(f"Failed to check file existence: {key}", original_error=e)
        except BotoCoreError as e:
            logger.error(f"Failed to check file existence in R2: {key}, error: {e}")
            raise StorageError(f"Failed to check file existence: {key}", original_error=e)

    async def get_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        method: str = "get_object",
    ) -> str:
        """
        Generate a presigned URL for temporary access to a file.

        Args:
            key: S3 object key (path in bucket)
            expiration: URL expiration time in seconds (default 1 hour)
            method: S3 method to presign (get_object, put_object, etc.)

        Returns:
            Presigned URL string

        Raises:
            StorageError: If URL generation fails
        """
        try:
            # Run presigned URL generation in thread pool
            loop = asyncio.get_event_loop()
            url = await loop.run_in_executor(
                None,
                lambda: self.s3_client.generate_presigned_url(
                    ClientMethod=method,
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": key,
                    },
                    ExpiresIn=expiration,
                ),
            )

            logger.info(f"Generated presigned URL for R2 file: {key}")
            return url

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to generate presigned URL for R2: {key}, error: {e}")
            raise StorageError(f"Failed to generate presigned URL: {key}", original_error=e)

    def get_public_url(self, key: str) -> str:
        """
        Get the public CDN URL for a file.

        Args:
            key: S3 object key (path in bucket)

        Returns:
            Public URL string
        """
        if self.public_url:
            # Use CDN URL if configured
            return urljoin(self.public_url.rstrip("/") + "/", key)

        # Fallback to R2 endpoint URL
        return f"{settings.R2_ENDPOINT}/{self.bucket_name}/{key}"

    async def copy_file(
        self,
        source_key: str,
        destination_key: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Copy a file within R2 storage.

        Args:
            source_key: Source S3 object key
            destination_key: Destination S3 object key
            metadata: Optional new metadata for destination object

        Returns:
            Public URL of copied file

        Raises:
            StorageError: If copy fails
        """
        try:
            # Prepare copy source
            copy_source = {
                "Bucket": self.bucket_name,
                "Key": source_key,
            }

            # Build extra args
            extra_args = {}
            if metadata is not None:
                extra_args["Metadata"] = metadata
                extra_args["MetadataDirective"] = "REPLACE"

            # Run S3 copy in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.copy_object(
                    Bucket=self.bucket_name,
                    CopySource=copy_source,
                    Key=destination_key,
                    **extra_args,
                ),
            )

            logger.info(f"Copied file in R2: {source_key} -> {destination_key}")
            return self.get_public_url(destination_key)

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to copy file in R2: {source_key} -> {destination_key}, error: {e}")
            raise StorageError(
                f"Failed to copy file: {source_key} -> {destination_key}",
                original_error=e,
            )
