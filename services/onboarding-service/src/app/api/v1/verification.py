"""
Email verification API endpoints.

Handles email verification and resend functionality.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.events.kafka_producer import KafkaProducer, get_kafka_producer
from src.app.middleware.auth import CurrentUser, get_current_user
from src.app.middleware.rate_limit import RateLimiter, get_rate_limiter, rate_limit_resend
from src.app.schemas.verification import (
    ResendVerificationRequest,
    ResendVerificationResponse,
    VerificationResponse,
    VerifyEmailRequest,
)
from src.app.services.verification_service import VerificationService

router = APIRouter(tags=["verification"])


@router.post(
    "/verify-email",
    response_model=VerificationResponse,
    summary="Verify email address",
    description="Verify email using token from verification email",
    responses={
        200: {"description": "Email verified successfully"},
        400: {"description": "Token expired or already used"},
        404: {"description": "Invalid token"},
    },
)
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
    kafka_producer: KafkaProducer = Depends(get_kafka_producer),
) -> VerificationResponse:
    """
    Verify user's email address with token.

    - Token is provided in the verification email link
    - Marks user's email as verified
    - Returns new access token with updated claims
    - Redirects to workspace setup
    """
    service = VerificationService(db, kafka_producer)
    return await service.verify_email(request.token)


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    summary="Resend verification email",
    description="Request a new verification email",
    responses={
        200: {"description": "Verification email sent"},
        409: {"description": "Email already verified"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def resend_verification(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ResendVerificationResponse:
    """
    Resend verification email.

    - Invalidates previous verification tokens
    - Generates new verification token
    - Sends new verification email

    Rate limited to 3 requests per user per hour.
    """
    # Note: Rate limiting by email is done inside the service
    # to avoid revealing if email exists
    service = VerificationService(db)
    result = await service.resend_verification_email(request)
    return ResendVerificationResponse(**result)
