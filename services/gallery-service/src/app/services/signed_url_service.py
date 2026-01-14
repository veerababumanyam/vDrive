"""Service for generating signed URLs for R2 assets."""

from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import boto3
from botocore.client import Config

from src.app.core.config import settings
from src.app.core.logging import logger


class SignedUrlService:
    """Service for generating signed URLs for asset access."""

    def __init__(self):
        """Initialize S3/R2 client."""
        self._s3_client = None

    def _get_s3_client(self):
        """Get or create S3 client (lazy initialization)."""
        if self._s3_client is None:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=settings.R2_ENDPOINT,
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                region_name=settings.R2_REGION,
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                ),
            )
            logger.debug("S3/R2 client initialized")
        return self._s3_client

    def generate_presigned_url(
        self,
        asset_id: str,
        bucket: str,
        object_key: str,
        expires_in: int = 3600,
        response_content_disposition: Optional[str] = None,
    ) -> str:
        """Generate a presigned URL for asset access.

        Args:
            asset_id: Asset UUID (for logging)
            bucket: S3/R2 bucket name
            object_key: Object key in bucket
            expires_in: URL expiration in seconds (default 1 hour)
            response_content_disposition: Optional Content-Disposition header

        Returns:
            Presigned URL string
        """
        try:
            client = self._get_s3_client()

            params = {
                "Bucket": bucket,
                "Key": object_key,
            }

            # Add content disposition if specified (for downloads)
            if response_content_disposition:
                params["ResponseContentDisposition"] = response_content_disposition

            url = client.generate_presigned_url(
                ClientMethod="get_object",
                Params=params,
                ExpiresIn=expires_in,
            )

            logger.debug(
                "Presigned URL generated",
                asset_id=asset_id,
                bucket=bucket,
                expires_in=expires_in,
            )

            return url

        except Exception as e:
            logger.error(
                "Failed to generate presigned URL",
                asset_id=asset_id,
                bucket=bucket,
                error=str(e),
            )
            raise

    def generate_asset_urls(
        self,
        asset_id: str,
        original_key: str,
        thumbnail_key: Optional[str] = None,
        lqip_key: Optional[str] = None,
        filename: Optional[str] = None,
        expires_in: int = 3600,
    ) -> dict[str, Optional[str]]:
        """Generate all URLs for an asset (original, thumbnail, LQIP).

        Args:
            asset_id: Asset UUID
            original_key: Object key for original image
            thumbnail_key: Optional object key for thumbnail
            lqip_key: Optional object key for LQIP
            filename: Optional filename for Content-Disposition
            expires_in: URL expiration in seconds

        Returns:
            Dict with asset_url, thumbnail_url, lqip_url
        """
        bucket = settings.R2_BUCKET_NAME

        # Generate original URL
        content_disposition = None
        if filename:
            content_disposition = f'inline; filename="{filename}"'

        asset_url = self.generate_presigned_url(
            asset_id=asset_id,
            bucket=bucket,
            object_key=original_key,
            expires_in=expires_in,
            response_content_disposition=content_disposition,
        )

        # Generate thumbnail URL
        thumbnail_url = None
        if thumbnail_key:
            thumbnail_url = self.generate_presigned_url(
                asset_id=asset_id,
                bucket=bucket,
                object_key=thumbnail_key,
                expires_in=expires_in,
            )

        # Generate LQIP URL
        lqip_url = None
        if lqip_key:
            lqip_url = self.generate_presigned_url(
                asset_id=asset_id,
                bucket=bucket,
                object_key=lqip_key,
                expires_in=expires_in,
            )

        return {
            "asset_url": asset_url,
            "thumbnail_url": thumbnail_url,
            "lqip_url": lqip_url,
        }


# Singleton instance
_signed_url_service = SignedUrlService()


def get_signed_url_service() -> SignedUrlService:
    """Get singleton SignedUrlService instance."""
    return _signed_url_service
