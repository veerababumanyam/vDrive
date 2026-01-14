"""Tests for SignedUrlService."""

import pytest
from unittest.mock import MagicMock

from src.app.services.signed_url_service import SignedUrlService, get_signed_url_service


class TestSignedUrlService:
    """Test signed URL generation service."""

    def test_get_signed_url_service_singleton(self):
        """Test get_signed_url_service returns singleton instance."""
        service1 = get_signed_url_service()
        service2 = get_signed_url_service()
        
        assert service1 is service2

    def test_generate_presigned_url_basic(self, mocker):
        """Test generating basic presigned URL without content disposition."""
        service = SignedUrlService()
        
        # Mock S3 client
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://example.com/signed-url"
        mocker.patch.object(service, "_get_s3_client", return_value=mock_client)
        
        # Generate URL
        url = service.generate_presigned_url(
            asset_id="test-asset-id",
            bucket="test-bucket",
            object_key="path/to/object.jpg",
            expires_in=3600,
        )
        
        assert url == "https://example.com/signed-url"
        mock_client.generate_presigned_url.assert_called_once_with(
            ClientMethod="get_object",
            Params={"Bucket": "test-bucket", "Key": "path/to/object.jpg"},
            ExpiresIn=3600,
        )

    def test_generate_presigned_url_with_content_disposition(self, mocker):
        """Test generating presigned URL with Content-Disposition header."""
        service = SignedUrlService()
        
        # Mock S3 client
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://example.com/signed-url-download"
        mocker.patch.object(service, "_get_s3_client", return_value=mock_client)
        
        # Generate URL with content disposition
        url = service.generate_presigned_url(
            asset_id="test-asset-id",
            bucket="test-bucket",
            object_key="path/to/download.jpg",
            expires_in=7200,
            response_content_disposition='attachment; filename="photo.jpg"',
        )
        
        assert url == "https://example.com/signed-url-download"
        
        # Verify Content-Disposition was added to params
        call_args = mock_client.generate_presigned_url.call_args
        assert call_args.kwargs["Params"]["ResponseContentDisposition"] == 'attachment; filename="photo.jpg"'

    def test_generate_presigned_url_exception_handling(self, mocker):
        """Test exception handling in generate_presigned_url."""
        service = SignedUrlService()
        
        # Mock S3 client to raise exception
        mock_client = MagicMock()
        mock_client.generate_presigned_url.side_effect = Exception("S3 connection failed")
        mocker.patch.object(service, "_get_s3_client", return_value=mock_client)
        
        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            service.generate_presigned_url(
                asset_id="test-asset-id",
                bucket="test-bucket",
                object_key="path/to/object.jpg",
            )
        
        assert "S3 connection failed" in str(exc_info.value)

    def test_generate_asset_urls_all_variants(self, mocker):
        """Test generating all asset URLs (original, thumbnail, LQIP)."""
        service = SignedUrlService()
        
        # Mock generate_presigned_url to return different URLs
        def mock_presigned_url(asset_id, bucket, object_key, expires_in, response_content_disposition=None):
            if "original" in object_key:
                return "https://example.com/original.jpg"
            elif "thumbnail" in object_key:
                return "https://example.com/thumbnail.jpg"
            elif "lqip" in object_key:
                return "https://example.com/lqip.jpg"
        
        mocker.patch.object(service, "generate_presigned_url", side_effect=mock_presigned_url)
        
        # Generate all URLs
        urls = service.generate_asset_urls(
            asset_id="test-asset-id",
            original_key="path/to/original.jpg",
            thumbnail_key="path/to/thumbnail.jpg",
            lqip_key="path/to/lqip.jpg",
            expires_in=3600,
        )
        
        assert urls["asset_url"] == "https://example.com/original.jpg"
        assert urls["thumbnail_url"] == "https://example.com/thumbnail.jpg"
        assert urls["lqip_url"] == "https://example.com/lqip.jpg"

    def test_generate_asset_urls_with_filename(self, mocker):
        """Test generating asset URLs with filename for Content-Disposition."""
        service = SignedUrlService()
        
        # Mock generate_presigned_url
        mock_presigned_url = mocker.patch.object(
            service, 
            "generate_presigned_url",
            return_value="https://example.com/asset.jpg"
        )
        
        # Generate URLs with filename
        urls = service.generate_asset_urls(
            asset_id="test-asset-id",
            original_key="path/to/asset.jpg",
            filename="my-photo.jpg",
            expires_in=3600,
        )
        
        # Verify Content-Disposition was passed for original URL
        first_call = mock_presigned_url.call_args_list[0]
        assert first_call.kwargs["response_content_disposition"] == 'inline; filename="my-photo.jpg"'

    def test_generate_asset_urls_optional_variants(self, mocker):
        """Test generating asset URLs with only original (no thumbnail/LQIP)."""
        service = SignedUrlService()
        
        mocker.patch.object(
            service, 
            "generate_presigned_url",
            return_value="https://example.com/original.jpg"
        )
        
        # Generate URLs without optional variants
        urls = service.generate_asset_urls(
            asset_id="test-asset-id",
            original_key="path/to/original.jpg",
            thumbnail_key=None,
            lqip_key=None,
            expires_in=3600,
        )
        
        assert urls["asset_url"] == "https://example.com/original.jpg"
        assert urls["thumbnail_url"] is None
        assert urls["lqip_url"] is None

    def test_s3_client_lazy_initialization(self):
        """Test S3 client is lazily initialized."""
        service = SignedUrlService()
        
        # Client should be None initially
        assert service._s3_client is None
        
        # Getting client should initialize it
        client1 = service._get_s3_client()
        assert client1 is not None
        
        # Getting client again should return same instance
        client2 = service._get_s3_client()
        assert client1 is client2
