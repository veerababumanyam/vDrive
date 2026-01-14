"""
Login API endpoints with comprehensive security features.

Handles email/password signin, Google OAuth, token refresh, and logout
with rate limiting, account lockout, and audit logging.
"""

from fastapi import APIRouter, Depends, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.database import get_db
from src.app.core.redis import get_redis
from src.app.core.security import create_access_token, create_refresh_token
from src.app.core.turnstile import verify_turnstile_safe
from src.app.middleware.error_handler import (
    AuthenticationError,
    RateLimitError,
    ValidationError,
)
from src.app.services.auth_service import AuthService
from src.app.schemas.auth import UserResponse

# Import will be added in Phase 3 (User Story 1)
# from src.app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(tags=["login"], prefix="/login")


# Helper functions
def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    # Check X-Forwarded-For header (if behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    # Fallback to direct client
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request."""
    return request.headers.get("User-Agent", "unknown")


# ==========================================
# Phase 3: User Story 1 - Email/Password Signin
# ==========================================

@router.post(
    "",
    response_model="LoginResponse",
    status_code=status.HTTP_200_OK,
    summary="Sign in with email and password",
    description="Authenticate user with email and password, with rate limiting and security checks",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials or account locked"},
        403: {"description": "Email not verified or account disabled"},
        429: {"description": "Too many login attempts"},
    },
)
async def login(
    request_body: "LoginRequest",
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Authenticate user with email and password.

    Security features:
    - Rate limiting (5 attempts per 15 minutes per IP)
    - Account lockout (5 failed attempts = 30 min lockout)
    - Email verification requirement
    - Account status check
    - Cloudflare Turnstile bot protection
    - Comprehensive audit logging
    - HttpOnly secure refresh token cookie

    Returns:
    - JWT access token (15 min expiry)
    - Refresh token in HttpOnly cookie (7 or 30 days)
    - User profile information
    """
    # Import here to avoid circular dependencies
    from src.app.schemas.auth import LoginRequest, LoginResponse, UserResponse

    # Cast request_body to proper type
    login_req: LoginRequest = request_body

    # Extract client context
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Initialize auth service
    auth_service = AuthService(db, redis)

    try:
        # 1. Check rate limiting (T021)
        await auth_service.check_rate_limit(client_ip)

        # 2. Verify Turnstile token if provided (T018)
        if login_req.turnstile_token:
            is_valid = await verify_turnstile_safe(
                login_req.turnstile_token,
                client_ip
            )
            if not is_valid:
                await auth_service.increment_rate_limit(client_ip)
                raise ValidationError("Bot protection verification failed")

        # 3. Authenticate user (includes T022, T023, T024 checks)
        user = await auth_service.authenticate_user(
            email=login_req.email,
            password=login_req.password,
            ip_address=client_ip,
        )

        # 4. Create session in Redis (T020)
        session_id = await auth_service.create_session(
            user_id=str(user.id),
            device_info=user_agent,
            ip_address=client_ip,
            remember_me=login_req.remember_me,
        )

        # 5. Create tokens
        access_token_expires = 15 * 60  # 15 minutes in seconds
        refresh_token_expires_days = 30 if login_req.remember_me else 7

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "type": "access",
            }
        )

        refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
                "type": "refresh",
                "session_id": session_id,
            },
            expires_days=refresh_token_expires_days,
        )

        # 6. Set HttpOnly Secure cookie for refresh token (T020)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # HTTPS only
            samesite="strict",  # CSRF protection (T080)
            max_age=refresh_token_expires_days * 24 * 60 * 60,
        )

        # 7. Log successful login (T025)
        await auth_service.log_auth_event(
            event_type="LOGIN_SUCCESS",
            result="success",
            user_id=str(user.id),
            ip_address=client_ip,
            user_agent=user_agent,
            session_id=session_id,
            metadata={
                "remember_me": login_req.remember_me,
            },
        )

        # 8. Return response
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=access_token_expires,
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                avatar_url=user.avatar_url,
                email_verified=user.email_verified,
            ),
        )

    except (AuthenticationError, ValidationError, RateLimitError) as e:
        # Increment rate limit on failure
        await auth_service.increment_rate_limit(client_ip)

        # Log failed attempt (T025)
        await auth_service.log_auth_event(
            event_type="LOGIN_FAILED",
            result="failure",
            email_attempted=login_req.email,
            ip_address=client_ip,
            user_agent=user_agent,
            metadata={"reason": str(e)},
        )

        raise


# Phase 4 (User Story 2):
# - GET /oauth/google/signin - Initiate Google OAuth signin
# - GET /oauth/google/signin/callback - Handle OAuth callback

# Phase 5 (User Story 3):
# - POST /refresh - Refresh access token using refresh token cookie

# Phase 6 (User Story 4):
# - POST /logout - Logout current session
# - POST /logout/all - Logout all devices

# Placeholder endpoints

@router.get("/health", summary="Login API health check")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "login"}
