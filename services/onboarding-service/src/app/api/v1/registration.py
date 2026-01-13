"""
Registration API endpoints.

Handles user registration and email availability checking.
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.events.kafka_producer import KafkaProducer, get_kafka_producer
from src.app.middleware.rate_limit import get_client_ip, rate_limit_registration
from src.app.schemas.registration import (
    EmailCheckRequest,
    EmailCheckResponse,
    RegistrationRequest,
    RegistrationResponse,
)
from src.app.services.registration_service import RegistrationService

router = APIRouter(tags=["registration"])


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Validation error"},
        409: {"description": "Email already exists"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def register_user(
    request: RegistrationRequest,
    http_request: Request,
    _: None = Depends(rate_limit_registration),
    db: AsyncSession = Depends(get_db),
    kafka_producer: KafkaProducer = Depends(get_kafka_producer),
) -> RegistrationResponse:
    """
    Register a new user account.

    - Validates Cloudflare Turnstile token for bot protection
    - Checks email uniqueness
    - Creates user with hashed password
    - Sends verification email
    - Returns JWT access token for immediate use

    Rate limited to 5 attempts per IP per 15 minutes.
    """
    client_ip = get_client_ip(http_request)
    service = RegistrationService(db, kafka_producer)
    return await service.register_user(request, client_ip)


@router.get(
    "/check-email",
    response_model=EmailCheckResponse,
    summary="Check email availability",
    description="Check if an email address is available for registration",
    responses={
        200: {"description": "Email availability status"},
        400: {"description": "Invalid email format"},
    },
)
async def check_email_availability(
    email: str,
    db: AsyncSession = Depends(get_db),
) -> EmailCheckResponse:
    """
    Check if email address is available for registration.

    Returns availability status and message.
    Note: This endpoint reveals email existence for UX during registration form.
    For security-sensitive flows, use the obfuscated response pattern.
    """
    # Normalize email to lowercase for consistent checking
    email = email.lower().strip()
    service = RegistrationService(db)
    return await service.check_email_availability(email)
