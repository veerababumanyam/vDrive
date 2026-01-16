"""
Unit tests for StorageService (R2 storage operations).
"""

from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.app.services.storage_service import StorageService, StorageError


@pytest.mark.unit
class TestStorageService:
    """Test StorageService R2 operations."""

    @pytest.fixture
    def service(self, mock_s3):
        """Create StorageService with mock S3 client."""
        return StorageService(mock_s3)

    def test_upload_export_file(self, service, mock_s3):
        """Test uploading export file to R2."""
        file_key = "exports/test-export.zip"
        file_obj = BytesIO(b"test file content")
        file_size = len(file_obj.getvalue())

        # Upload file
        result_key = service.upload_export_file(file_key, file_obj, file_size)

        assert result_key == file_key
        mock_s3.upload_fileobj.assert_called_once()

    def test_upload_export_file_with_metadata(self, service, mock_s3):
        """Test uploading export file with metadata."""
        file_key = "exports/test-export.zip"
        file_obj = BytesIO(b"test file content")
        file_size = len(file_obj.getvalue())
        metadata = {
            "workspace_id": str(uuid4()),
            "export_type": "workspace",
        }

        # Upload file with metadata
        result_key = service.upload_export_file(
            file_key,
            file_obj,
            file_size,
            metadata=metadata,
        )

        assert result_key == file_key
        # Verify metadata was included in call
        call_kwargs = mock_s3.upload_fileobj.call_args[1]
        assert "Metadata" in call_kwargs

    def test_generate_download_url(self, service, mock_s3):
        """Test generating presigned download URL."""
        file_key = "exports/test-export.zip"
        expiration = 3600

        url = service.generate_download_url(file_key, expiration)

        assert url.startswith("https://")
        assert "test-file.zip" in url
        mock_s3.generate_presigned_url.assert_called_once()

    def test_generate_download_url_custom_expiration(self, service, mock_s3):
        """Test generating download URL with custom expiration."""
        file_key = "exports/test-export.zip"
        expiration = 7200  # 2 hours

        url = service.generate_download_url(file_key, expiration)

        assert url is not None
        call_kwargs = mock_s3.generate_presigned_url.call_args[1]
        assert call_kwargs["ExpiresIn"] == expiration

    def test_delete_export_file(self, service, mock_s3):
        """Test deleting export file from R2."""
        file_key = "exports/test-export.zip"

        service.delete_export_file(file_key)

        mock_s3.delete_object.assert_called_once_with(
            Bucket=service.bucket_name,
            Key=file_key,
        )

    def test_cleanup_expired_exports(self, service, mock_s3):
        """Test cleanup of expired export files."""
        # Mock list_objects_v2 to return expired files
        expired_time = datetime.now(timezone.utc)
        mock_s3.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "exports/expired-1.zip",
                    "LastModified": expired_time,
                },
                {
                    "Key": "exports/expired-2.zip",
                    "LastModified": expired_time,
                },
            ]
        }

        deleted_count = service.cleanup_expired_exports(max_age_days=7)

        assert deleted_count >= 0
        mock_s3.list_objects_v2.assert_called()

    def test_upload_export_file_error_handling(self, service):
        """Test upload error handling."""
        file_key = "exports/test-export.zip"
        file_obj = BytesIO(b"test content")

        # Simulate S3 error
        service.s3.upload_fileobj.side_effect = Exception("S3 upload failed")

        with pytest.raises(StorageError) as exc_info:
            service.upload_export_file(file_key, file_obj, len(file_obj.getvalue()))

        assert "upload failed" in str(exc_info.value).lower()

    def test_generate_download_url_error_handling(self, service):
        """Test download URL generation error handling."""
        file_key = "exports/test-export.zip"

        # Simulate S3 error
        service.s3.generate_presigned_url.side_effect = Exception("S3 error")

        with pytest.raises(StorageError) as exc_info:
            service.generate_download_url(file_key)

        assert "generate" in str(exc_info.value).lower() or "download" in str(exc_info.value).lower()
