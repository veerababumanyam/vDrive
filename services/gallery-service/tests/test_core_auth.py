"""Tests for JWT authentication utilities."""

from datetime import timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from src.app.core.auth import (
    create_gallery_access_token,
    extract_magic_link_token,
    verify_token,
)
from src.app.core.config import settings


@pytest.fixture(autouse=True)
def override_jwt_algorithm():
    """Override JWT algorithm to HS256 for testing (python-jose doesn't support EdDSA)."""
    original_algorithm = settings.JWT_ALGORITHM
    settings.JWT_ALGORITHM = "HS256"
    yield
    settings.JWT_ALGORITHM = original_algorithm


class TestCreateGalleryAccessToken:
    """Test gallery access token creation."""

    def test_create_token_default_expiry(self):
        """Test creating token with default 24-hour expiry."""
        gallery_id = "00000000-0000-0000-0000-000000000123"
        link_id = "test-magic-link-id"

        token = create_gallery_access_token(gallery_id, link_id)

        # Should return a string token
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify payload
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        assert payload["type"] == "gallery_access"
        assert payload["gallery_id"] == gallery_id
        assert payload["link_id"] == link_id
        assert "exp" in payload
        assert "iat" in payload

    def test_create_token_custom_expiry(self):
        """Test creating token with custom expiry."""
        gallery_id = "00000000-0000-0000-0000-000000000456"
        link_id = "custom-expiry-link"
        custom_delta = timedelta(hours=1)

        token = create_gallery_access_token(gallery_id, link_id, custom_delta)

        # Verify token
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        assert payload["gallery_id"] == gallery_id
        assert payload["link_id"] == link_id

        # Verify expiry is roughly 1 hour from now (within 10 seconds tolerance)
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]
        diff = exp_timestamp - iat_timestamp
        assert 3590 < diff < 3610  # ~1 hour (3600 seconds ± 10 seconds)


class TestVerifyToken:
    """Test token verification."""

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        gallery_id = "00000000-0000-0000-0000-000000000789"
        link_id = "valid-token-link"

        # Create token
        token = create_gallery_access_token(gallery_id, link_id)

        # Verify token
        payload = verify_token(token, expected_type="gallery_access")

        assert payload["gallery_id"] == gallery_id
        assert payload["link_id"] == link_id
        assert payload["type"] == "gallery_access"

    def test_verify_invalid_token(self):
        """Test verifying an invalid token raises exception."""
        invalid_token = "invalid.jwt.token"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token, expected_type="gallery_access")

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    def test_verify_wrong_token_type(self):
        """Test verifying token with wrong type raises exception."""
        gallery_id = "00000000-0000-0000-0000-000000000999"
        link_id = "wrong-type-link"

        # Create gallery_access token
        token = create_gallery_access_token(gallery_id, link_id)

        # Try to verify as 'access' type (wrong type)
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, expected_type="access")

        assert exc_info.value.status_code == 401
        assert "Invalid token type" in exc_info.value.detail
        assert "expected access" in exc_info.value.detail
        assert "got gallery_access" in exc_info.value.detail

    def test_verify_expired_token(self):
        """Test verifying an expired token raises exception."""
        gallery_id = "00000000-0000-0000-0000-000000000abc"
        link_id = "expired-token-link"

        # Create token that expires immediately
        token = create_gallery_access_token(
            gallery_id, link_id, expires_delta=timedelta(seconds=-1)
        )

        # Verify expired token
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, expected_type="gallery_access")

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail


class TestExtractMagicLinkToken:
    """Test magic link token extraction."""

    def test_extract_valid_link_id(self):
        """Test extracting a valid link ID."""
        valid_link_id = "abcdef1234567890"  # 16+ characters

        result = extract_magic_link_token(valid_link_id)

        assert result == valid_link_id

    def test_extract_long_link_id(self):
        """Test extracting a long link ID."""
        long_link_id = "a" * 100  # Very long ID

        result = extract_magic_link_token(long_link_id)

        assert result == long_link_id

    def test_extract_exactly_16_chars(self):
        """Test extracting exactly 16 character link ID (minimum)."""
        min_link_id = "1234567890123456"  # Exactly 16 chars

        result = extract_magic_link_token(min_link_id)

        assert result == min_link_id

    def test_extract_too_short_link_id(self):
        """Test extracting link ID that's too short raises exception."""
        short_link_id = "short123"  # Less than 16 chars

        with pytest.raises(HTTPException) as exc_info:
            extract_magic_link_token(short_link_id)

        assert exc_info.value.status_code == 400
        assert "Invalid Magic Link format" in exc_info.value.detail

    def test_extract_empty_link_id(self):
        """Test extracting empty link ID raises exception."""
        with pytest.raises(HTTPException) as exc_info:
            extract_magic_link_token("")

        assert exc_info.value.status_code == 400
        assert "Invalid Magic Link format" in exc_info.value.detail

    def test_extract_none_link_id(self):
        """Test extracting None link ID raises exception."""
        with pytest.raises(HTTPException) as exc_info:
            extract_magic_link_token(None)

        assert exc_info.value.status_code == 400
        assert "Invalid Magic Link format" in exc_info.value.detail


class TestGetCurrentUser:
    """Test get_current_user dependency function."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mocker):
        """Test get_current_user with valid access token."""
        from fastapi.security import HTTPAuthorizationCredentials
        from src.app.core.auth import get_current_user

        # Mock credentials
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )

        # Mock verify_token to return valid payload
        mocker.patch(
            "src.app.core.auth.verify_token",
            return_value={
                "sub": "user-123",
                "email": "test@example.com",
                "workspace_id": "workspace-456",
                "email_verified": True,
                "type": "access",
            }
        )

        # Get current user
        current_user = await get_current_user(mock_credentials)

        assert current_user.user_id == "user-123"
        assert current_user.email == "test@example.com"
        assert current_user.workspace_id == "workspace-456"
        assert current_user.email_verified is True
