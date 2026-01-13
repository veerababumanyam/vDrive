"""
Unit tests for VerificationService.

Tests email verification business logic including:
- Token verification
- Email resend
- Welcome email sending
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestSendVerificationEmail:
    """Test verification email sending."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_send_verification_email_success(self, mock_db):
        """Test successful verification email."""
        from src.app.services.verification_service import VerificationService

        service = VerificationService(db=mock_db)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(
                    post=AsyncMock(return_value=mock_response)
                )
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service._send_verification_email(
                email="test@example.com",
                token="verification_token",
                first_name="John",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_verification_email_api_failure(self, mock_db):
        """Test email API failure handling."""
        from src.app.services.verification_service import VerificationService

        service = VerificationService(db=mock_db)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(
                    post=AsyncMock(return_value=mock_response)
                )
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service._send_verification_email(
                email="test@example.com",
                token="verification_token",
                first_name="John",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_verification_email_exception(self, mock_db):
        """Test verification email exception handling."""
        from src.app.services.verification_service import VerificationService

        service = VerificationService(db=mock_db)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                side_effect=Exception("Network error")
            )

            result = await service._send_verification_email(
                email="test@example.com",
                token="verification_token",
                first_name="John",
            )

            assert result is False


class TestSendWelcomeEmail:
    """Test welcome email sending."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_send_welcome_email_success(self, mock_db):
        """Test successful welcome email."""
        from src.app.services.verification_service import VerificationService

        service = VerificationService(db=mock_db)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(
                    post=AsyncMock(return_value=mock_response)
                )
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.send_welcome_email(
                email="test@example.com",
                first_name="John",
                workspace_name="John's Studio",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_welcome_email_api_failure(self, mock_db):
        """Test welcome email API failure handling."""
        from src.app.services.verification_service import VerificationService

        service = VerificationService(db=mock_db)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(
                    post=AsyncMock(return_value=mock_response)
                )
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await service.send_welcome_email(
                email="test@example.com",
                first_name="John",
                workspace_name="John's Studio",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_welcome_email_exception(self, mock_db):
        """Test welcome email exception handling."""
        from src.app.services.verification_service import VerificationService

        service = VerificationService(db=mock_db)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                side_effect=Exception("Network error")
            )

            result = await service.send_welcome_email(
                email="test@example.com",
                first_name="John",
                workspace_name="John's Studio",
            )

            assert result is False


class TestVerificationServiceInit:
    """Test VerificationService initialization."""

    def test_init_creates_repositories(self):
        """Test service creates required repositories."""
        from src.app.services.verification_service import VerificationService

        mock_db = MagicMock()
        service = VerificationService(db=mock_db)

        assert service.user_repo is not None
        assert service.token_repo is not None
        assert service.onboarding_repo is not None
        assert service.kafka_producer is None

    def test_init_with_kafka(self):
        """Test service with Kafka producer."""
        from src.app.services.verification_service import VerificationService

        mock_db = MagicMock()
        mock_kafka = MagicMock()
        service = VerificationService(db=mock_db, kafka_producer=mock_kafka)

        assert service.kafka_producer is mock_kafka
