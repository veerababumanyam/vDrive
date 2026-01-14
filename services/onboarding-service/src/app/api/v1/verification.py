"""
Email verification API endpoints.

Handles email verification and resend functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.database import get_db
from src.app.core.redis import RedisKeys
from src.app.events.kafka_producer import KafkaProducer, get_kafka_producer
from src.app.middleware.rate_limit import RateLimiter, get_client_ip, get_rate_limiter
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
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ResendVerificationResponse:
    """
    Resend verification email.

    - Invalidates previous verification tokens
    - Generates new verification token
    - Sends new verification email

    Rate limited to 3 requests per IP per hour.
    """
    # Rate limit by IP to prevent abuse while not revealing email existence
    ip = get_client_ip(http_request)
    key = RedisKeys.rate_limit_resend(ip)

    allowed, remaining, retry_after = await rate_limiter.check_rate_limit(
        key=key,
        max_requests=settings.RATE_LIMIT_RESEND_MAX,
        window_seconds=settings.RATE_LIMIT_RESEND_WINDOW_SECONDS,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RateLimitExceeded",
                "message": "Too many resend requests. Please wait before trying again.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    service = VerificationService(db)
    result = await service.resend_verification_email(request)
    return ResendVerificationResponse(**result)
