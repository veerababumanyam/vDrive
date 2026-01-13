"""
Registration service for user signup business logic.
"""

from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

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

        # 9. Create access token
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "email_verified": False,
            }
        )

        # Note: Verification email is sent by the calling endpoint after registration
        # The endpoint uses VerificationService.send_verification_email for this

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
