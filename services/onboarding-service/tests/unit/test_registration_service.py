"""
Unit tests for RegistrationService.

Tests registration business logic including:
- User registration flow
- Email availability checks
- Turnstile validation
- Email verification token creation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.app.middleware.error_handler import ConflictError, ValidationError
from src.app.services.registration_service import RegistrationService
from src.app.schemas.registration import RegistrationRequest


class TestRegisterUser:
    """Test user registration flow."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.fixture
    def mock_kafka_producer(self):
        """Create mock Kafka producer."""
        producer = MagicMock()
        producer.publish_user_registered = AsyncMock()
        return producer

    @pytest.fixture
    def valid_registration_request(self):
        """Create valid registration request."""
        return RegistrationRequest(
            email="test@example.com",
            password="SecureP@ss123!",
            first_name="John",
            last_name="Doe",
            business_name="John's Studio",
            turnstile_token="valid-token",
            agree_to_terms=True,
            agree_to_privacy=True,
        )

    @pytest.mark.asyncio
    async def test_register_user_success(
        self,
        mock_db,
        mock_kafka_producer,
        valid_registration_request,
    ):
        """Test successful user registration."""
        user_id = str(uuid4())

        with patch(
            "src.app.services.registration_service.verify_turnstile_safe",
            new=AsyncMock(return_value=True),
        ), patch(
            "src.app.services.registration_service.hash_password",
            return_value="hashed_password",
        ), patch(
            "src.app.services.registration_service.generate_verification_token",
            return_value="verification_token",
        ), patch(
            "src.app.services.registration_service.hash_token",
            return_value="hashed_token",
        ), patch(
            "src.app.services.registration_service.create_access_token",
            return_value="access_token",
        ):
            service = RegistrationService(db=mock_db, kafka_producer=mock_kafka_producer)

            # Mock repositories
            mock_user = MagicMock()
            mock_user.id = user_id
            mock_user.email = valid_registration_request.email
            mock_user.first_name = valid_registration_request.first_name
            mock_user.last_name = valid_registration_request.last_name

            service.user_repo.email_exists = AsyncMock(return_value=False)
            service.user_repo.create = AsyncMock(return_value=mock_user)
            service.token_repo.create = AsyncMock()
            service.onboarding_repo.create = AsyncMock()
            service._send_verification_email = AsyncMock(return_value=True)

            result = await service.register_user(valid_registration_request, "127.0.0.1")

            assert result.user_id == user_id
            assert result.email == valid_registration_request.email
            assert result.email_verified is False
            assert result.access_token == "access_token"
            assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_register_user_turnstile_failure(
        self,
        mock_db,
        valid_registration_request,
    ):
        """Test registration fails with invalid Turnstile token."""
        with patch(
            "src.app.services.registration_service.verify_turnstile_safe",
            new=AsyncMock(return_value=False),
        ):
            service = RegistrationService(db=mock_db)

            with pytest.raises(ValidationError) as exc_info:
                await service.register_user(valid_registration_request, "127.0.0.1")

            assert "Bot verification failed" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_register_user_email_exists(
        self,
        mock_db,
        valid_registration_request,
    ):
        """Test registration fails when email already exists."""
        with patch(
            "src.app.services.registration_service.verify_turnstile_safe",
            new=AsyncMock(return_value=True),
        ):
            service = RegistrationService(db=mock_db)
            service.user_repo.email_exists = AsyncMock(return_value=True)

            with pytest.raises(ConflictError) as exc_info:
                await service.register_user(valid_registration_request, "127.0.0.1")

            assert "email already exists" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_register_user_without_kafka(
        self,
        mock_db,
        valid_registration_request,
    ):
        """Test registration succeeds without Kafka producer."""
        user_id = str(uuid4())

        with patch(
            "src.app.services.registration_service.verify_turnstile_safe",
            new=AsyncMock(return_value=True),
        ), patch(
            "src.app.services.registration_service.hash_password",
            return_value="hashed_password",
        ), patch(
            "src.app.services.registration_service.generate_verification_token",
            return_value="verification_token",
        ), patch(
            "src.app.services.registration_service.hash_token",
            return_value="hashed_token",
        ), patch(
            "src.app.services.registration_service.create_access_token",
            return_value="access_token",
        ):
            # No Kafka producer
            service = RegistrationService(db=mock_db, kafka_producer=None)

            mock_user = MagicMock()
            mock_user.id = user_id
            mock_user.email = valid_registration_request.email
            mock_user.first_name = valid_registration_request.first_name
            mock_user.last_name = valid_registration_request.last_name

            service.user_repo.email_exists = AsyncMock(return_value=False)
            service.user_repo.create = AsyncMock(return_value=mock_user)
            service.token_repo.create = AsyncMock()
            service.onboarding_repo.create = AsyncMock()
            service._send_verification_email = AsyncMock(return_value=True)

            result = await service.register_user(valid_registration_request, "127.0.0.1")

            assert result.user_id == user_id
            assert result.email_verified is False


class TestCheckEmailAvailability:
    """Test email availability checking."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_email_available(self, mock_db):
        """Test email is available when not in database."""
        service = RegistrationService(db=mock_db)
        service.user_repo.email_exists = AsyncMock(return_value=False)

        result = await service.check_email_availability("new@example.com")

        assert result.available is True
        assert "available" in result.message.lower()

    @pytest.mark.asyncio
    async def test_email_not_available(self, mock_db):
        """Test email is not available when exists in database."""
        service = RegistrationService(db=mock_db)
        service.user_repo.email_exists = AsyncMock(return_value=True)

        result = await service.check_email_availability("existing@example.com")

        assert result.available is False
        assert "already exists" in result.message.lower()


class TestSendVerificationEmail:
    """Test verification email sending."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_send_verification_email_success(self, mock_db):
        """Test successful verification email sending."""
        service = RegistrationService(db=mock_db)

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
    async def test_send_verification_email_failure(self, mock_db):
        """Test verification email failure handling."""
        service = RegistrationService(db=mock_db)

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
        service = RegistrationService(db=mock_db)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                side_effect=Exception("Connection error")
            )

            result = await service._send_verification_email(
                email="test@example.com",
                token="verification_token",
                first_name="John",
            )

            assert result is False
