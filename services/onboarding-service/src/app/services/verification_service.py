"""
Email verification service for handling verification tokens.
"""

from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.security import (
    create_access_token,
    generate_verification_token,
    hash_token,
)
from src.app.events.kafka_producer import EmailVerifiedEvent, KafkaProducer
from src.app.middleware.error_handler import (
    ConflictError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from src.app.models.onboarding_state import OnboardingStep
from src.app.repositories.onboarding_state_repository import OnboardingStateRepository
from src.app.repositories.user_repository import UserRepository
from src.app.repositories.verification_token_repository import VerificationTokenRepository
from src.app.schemas.verification import ResendVerificationRequest, VerificationResponse


class VerificationService:
    """
    Service for email verification business logic.

    Handles token verification, resend logic, and email delivery.
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

    async def verify_email(self, token: str) -> VerificationResponse:
        """
        Verify user email with token.

        Steps:
        1. Hash token and lookup
        2. Check token validity (not expired, not used)
        3. Mark email as verified
        4. Mark token as used
        5. Update onboarding state
        6. Publish EmailVerifiedEvent
        7. Return new access token

        Args:
            token: Plain text verification token from email link

        Returns:
            VerificationResponse with updated user info

        Raises:
            ValidationError: If token is invalid or expired
            NotFoundError: If token not found
        """
        # 1. Hash token and lookup
        token_hash = hash_token(token)
        verification_token = await self.token_repo.get_valid_by_token_hash(token_hash)

        # 2. Check token validity
        if verification_token is None:
            # Check if token exists but is invalid
            any_token = await self.token_repo.get_by_token_hash(token_hash)
            if any_token:
                if any_token.is_used:
                    raise ValidationError(
                        message="This verification link has already been used",
                        details=[{"field": "token", "message": "Token already used"}],
                    )
                elif any_token.is_expired:
                    raise ValidationError(
                        message="This verification link has expired. Please request a new one.",
                        details=[{"field": "token", "message": "Token expired"}],
                    )

            raise NotFoundError(message="Invalid verification link")

        # 3. Mark email as verified
        user = await self.user_repo.mark_email_verified(verification_token.user_id)
        if not user:
            raise NotFoundError(message="User not found")

        # 4. Mark token as used
        await self.token_repo.mark_used(verification_token.id)

        # 5. Update onboarding state
        await self.onboarding_repo.advance_step(
            user_id=user.id,
            new_step=OnboardingStep.WORKSPACE_IDENTITY,
            completed_step=OnboardingStep.EMAIL_VERIFICATION.value,
        )

        # 6. Commit transaction
        await self.db.commit()

        # 7. Publish event (non-blocking)
        if self.kafka_producer:
            event = EmailVerifiedEvent(
                user_id=user.id,
                email=user.email,
                verification_method="token",
            )
            await self.kafka_producer.publish_email_verified(event)

        # 8. Create new access token with verified status
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "email_verified": True,
            }
        )

        return VerificationResponse(
            user_id=user.id,
            email=user.email,
            email_verified=True,
            message="Email verified successfully",
            access_token=access_token,
            redirect_url="/onboarding/workspace",
        )

    async def resend_verification_email(
        self,
        request: ResendVerificationRequest,
    ) -> dict:
        """
        Resend verification email to user.

        Steps:
        1. Find user by email
        2. Check email not already verified
        3. Delete old verification tokens
        4. Generate new token
        5. Send verification email

        Args:
            request: Resend request with email

        Returns:
            Success message dict

        Raises:
            NotFoundError: If user not found
            ConflictError: If email already verified
        """
        # 1. Find user by email
        user = await self.user_repo.get_by_email(request.email)
        if not user:
            # Don't reveal if email exists - security best practice
            return {
                "message": "If an account exists with this email, a verification link has been sent.",
                "email": request.email,
            }

        # 2. Check email not already verified
        if user.email_verified:
            raise ConflictError(
                message="Email is already verified",
                details=[{"field": "email", "message": "Already verified"}],
            )

        # 3. Delete old verification tokens
        await self.token_repo.delete_by_user_id(user.id)

        # 4. Generate new token
        plain_token = generate_verification_token()
        token_hash = hash_token(plain_token)
        await self.token_repo.create(
            user_id=user.id,
            token_hash=token_hash,
        )

        # 5. Commit transaction
        await self.db.commit()

        # 6. Send verification email
        await self._send_verification_email(user.email, plain_token, user.first_name)

        return {
            "message": "Verification email sent. Please check your inbox.",
            "email": user.email,
        }

    async def send_verification_email(
        self,
        user_id: str,
        email: str,
        token: str,
        first_name: str,
    ) -> bool:
        """
        Send verification email via notification service.

        Args:
            user_id: User UUID
            email: Email address
            token: Plain text verification token
            first_name: User's first name for personalization

        Returns:
            True if sent successfully
        """
        return await self._send_verification_email(email, token, first_name)

    async def _send_verification_email(
        self,
        email: str,
        token: str,
        first_name: str,
    ) -> bool:
        """
        Internal method to send verification email.

        Args:
            email: Email address
            token: Plain text verification token
            first_name: User's first name

        Returns:
            True if sent successfully
        """
        import logging

        logger = logging.getLogger(__name__)
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
            # Log error but don't fail - email delivery is best-effort
            logger.error(
                "Error sending verification email",
                extra={"email": email, "error": str(e)},
                exc_info=True,
            )
            return False

    async def send_welcome_email(
        self,
        email: str,
        first_name: str,
        workspace_name: str,
    ) -> bool:
        """
        Send welcome email after onboarding completion.

        Args:
            email: Email address
            first_name: User's first name
            workspace_name: Created workspace name

        Returns:
            True if sent successfully
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/email/send",
                    json={
                        "to": email,
                        "template": "welcome",
                        "data": {
                            "first_name": first_name,
                            "workspace_name": workspace_name,
                            "dashboard_url": f"{settings.APP_URL}/dashboard",
                            "help_url": f"{settings.WEBSITE_URL}/help",
                        },
                    },
                )
                if response.status_code != 200:
                    logger.warning(
                        "Failed to send welcome email",
                        extra={
                            "email": email,
                            "status_code": response.status_code,
                        },
                    )
                return response.status_code == 200
        except Exception as e:
            logger.error(
                "Error sending welcome email",
                extra={"email": email, "error": str(e)},
                exc_info=True,
            )
            return False
