"""
Registration service for user signup business logic.
"""

import logging
from typing import Dict, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.security import (
    create_access_token,
    generate_verification_token,
    hash_password,
    hash_token,
)
from src.app.core.turnstile import verify_turnstile_safe
from src.app.events.kafka_producer import KafkaProducer, UserRegisteredEvent
from src.app.middleware.error_handler import ConflictError, ValidationError
from src.app.models.onboarding_state import OnboardingStep
from src.app.repositories.onboarding_state_repository import OnboardingStateRepository
from src.app.repositories.user_repository import UserRepository
from src.app.repositories.verification_token_repository import VerificationTokenRepository
from src.app.schemas.registration import (
    EmailCheckResponse,
    RegistrationRequest,
    RegistrationResponse,
)

logger = logging.getLogger(__name__)


class RegistrationService:
    """
    Service for user registration business logic.

    Handles registration flow, email verification token creation,
    and event publishing.
    """

    def __init__(
        self,
        db: AsyncSession,
        kafka_producer: Optional[KafkaProducer] = None,
    ):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = VerificationTokenRepository(db)
        self.onboarding_repo = OnboardingStateRepository(db)
        self.kafka_producer = kafka_producer

    async def register_user(
        self,
        request: RegistrationRequest,
        client_ip: Optional[str] = None,
    ) -> RegistrationResponse:
        """
        Register a new user.

        Steps:
        1. Validate Turnstile token
        2. Check email uniqueness
        3. Hash password
        4. Create user record
        5. Create verification token
        6. Create onboarding state
        7. Publish UserRegisteredEvent
        8. Return access token

        Args:
            request: Registration request data
            client_ip: Client IP for Turnstile verification

        Returns:
            RegistrationResponse with user info and access token

        Raises:
            ValidationError: If Turnstile verification fails
            ConflictError: If email already exists
        """
        # 1. Validate Turnstile token
        turnstile_valid = await verify_turnstile_safe(
            request.turnstile_token,
            client_ip,
        )
        if not turnstile_valid:
            raise ValidationError(
                message="Bot verification failed. Please try again.",
                details=[{"field": "turnstile_token", "message": "Invalid verification token"}],
            )

        # 2. Check email uniqueness
        if await self.user_repo.email_exists(request.email):
            raise ConflictError(
                message="An account with this email already exists",
                details=[{"field": "email", "message": "Email already registered"}],
            )

        # 3. Hash password
        password_hash = hash_password(request.password)

        # 4. Create user record
        user = await self.user_repo.create(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password_hash=password_hash,
            email_verified=False,
            terms_accepted=request.agree_to_terms,
            privacy_accepted=request.agree_to_privacy,
        )

        # 5. Create verification token
        plain_token = generate_verification_token()
        token_hash = hash_token(plain_token)
        await self.token_repo.create(
            user_id=user.id,
            token_hash=token_hash,
        )

        # 6. Create onboarding state
        await self.onboarding_repo.create(
            user_id=user.id,
            current_step=OnboardingStep.EMAIL_VERIFICATION,
            completed_steps=[OnboardingStep.REGISTRATION.value],
            form_data={
                "business_name": request.business_name,
                "email": request.email,
                "first_name": request.first_name,
                "last_name": request.last_name,
            },
        )

        # 7. Commit transaction
        await self.db.commit()

        # 8. Publish event (non-blocking)
        if self.kafka_producer:
            event = UserRegisteredEvent(
                user_id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                registration_method="email",
                email_verified=False,
            )
            await self.kafka_producer.publish_user_registered(event)

        # 9. Send verification email (non-blocking, best-effort)
        await self._send_verification_email(
            email=user.email,
            token=plain_token,
            first_name=user.first_name,
        )

        # 10. Create access token
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "email_verified": False,
            }
        )

        return RegistrationResponse(
            user_id=user.id,
            email=user.email,
            email_verified=False,
            message="Registration successful. Please check your email to verify your account.",
            access_token=access_token,
            token_type="bearer",
        )

    async def check_email_availability(self, email: str) -> EmailCheckResponse:
        """
        Check if an email address is available for registration.

        Args:
            email: Email address to check

        Returns:
            EmailCheckResponse with availability status
        """
        exists = await self.user_repo.email_exists(email)

        if exists:
            return EmailCheckResponse(
                available=False,
                message="An account with this email already exists",
            )

        return EmailCheckResponse(
            available=True,
            message="Email is available",
        )

    async def _send_verification_email(
        self,
        email: str,
        token: str,
        first_name: str,
    ) -> bool:
        """
        Send verification email via notification service.

        This is a best-effort operation - failures are logged but don't
        block registration. Users can request resend if needed.

        Args:
            email: Email address to send to
            token: Plain text verification token
            first_name: User's first name for personalization

        Returns:
            True if sent successfully, False otherwise
        """
        verification_url = f"{settings.APP_URL}/verify-email?token={token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/email/send",
                    json={
                        "to": email,
                        "template": "email_verification",
                        "data": {
                            "first_name": first_name,
                            "verification_url": verification_url,
                            "expires_in_hours": settings.EMAIL_VERIFICATION_EXPIRE_HOURS,
                        },
                    },
                )
                if response.status_code != 200:
                    logger.warning(
                        "Failed to send verification email",
                        extra={
                            "email": email,
                            "status_code": response.status_code,
                            "response": response.text[:200],
                        },
                    )
                return response.status_code == 200
        except Exception as e:
            # Log error but don't fail registration - email delivery is best-effort
            logger.error(
                "Error sending verification email",
                extra={"email": email, "error": str(e)},
                exc_info=True,
            )
            return False
