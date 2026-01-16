"""
Login API endpoints with comprehensive security features.

Handles email/password signin, Google OAuth, token refresh, and logout
with rate limiting, account lockout, and audit logging.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.database import get_db
from src.app.core.redis import get_redis
from src.app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_oauth_state,
    verify_token,
)
from src.app.core.turnstile import verify_turnstile_safe
from src.app.middleware.error_handler import (
    AuthenticationError,
    RateLimitError,
    ValidationError,
)
from src.app.services.auth_service import AuthService
from src.app.repositories.workspace_member_repository import WorkspaceMemberRepository
from src.app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
    UserResponse,
)

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
    response_model=LoginResponse,
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
    request_body: LoginRequest,
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
    # Use the request body directly
    login_req = request_body

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

        # 5. Get user's primary workspace for JWT token
        workspace_member_repo = WorkspaceMemberRepository(db)
        user_workspaces = await workspace_member_repo.get_user_workspaces(str(user.id))
        primary_workspace_id = str(user_workspaces[0].workspace_id) if user_workspaces else None

        # 6. Create tokens
        access_token_expires = 15 * 60  # 15 minutes in seconds
        refresh_token_expires_days = 30 if login_req.remember_me else 7

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "email_verified": user.email_verified,
                "workspace_id": primary_workspace_id,
            }
        )

        refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
                "type": "refresh",
                "session_id": session_id,
            },
            expires_delta=timedelta(days=refresh_token_expires_days),
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
                avatar_url=getattr(user, 'avatar_url', None),
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


# ==========================================
# Phase 4: User Story 2 - Google OAuth Signin
# ==========================================

@router.get(
    "/oauth/google/signin",
    response_model=dict,
    summary="Initiate Google OAuth signin",
    description="Start Google OAuth signin flow (for existing users)",
)
async def google_signin_init(
    request: Request,
    redis: Redis = Depends(get_redis),
):
    """
    Initiate Google OAuth signin flow.

    Creates OAuth state with "signin" flow type and returns Google authorization URL.
    User will be redirected to Google for authentication.

    T031: OAuth signin initiation endpoint
    T032: OAuth state storage with "signin" flow type
    """
    import json

    # Generate state token for CSRF protection (T031)
    state = generate_oauth_state()

    # Store state in Redis with "signin" flow type (T032)
    state_data = {
        "flow": "signin",  # Distinguish from registration
        "redirect_uri": "/dashboard",
        "created_at": datetime.utcnow().isoformat(),
    }
    key = f"oauth:state:{state}"
    await redis.setex(key, 600, json.dumps(state_data))  # 10 min TTL

    # Build Google authorization URL
    from urllib.parse import urlencode
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI.replace("/callback", "/signin/callback"),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    query_string = urlencode(params)
    redirect_url = f"{GOOGLE_AUTH_URL}?{query_string}"

    return {"redirect_url": redirect_url}


@router.get(
    "/oauth/google/signin/callback",
    response_model=LoginResponse,
    summary="Handle Google OAuth signin callback",
    description="Process OAuth callback for signin (existing users)",
    responses={
        200: {"description": "Signin successful"},
        302: {"description": "Redirect with error"},
        404: {"description": "Account not found - need to register first"},
    },
)
async def google_signin_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Handle Google OAuth signin callback.

    Flow for signin (not registration):
    1. Validate OAuth state
    2. Exchange code for tokens
    3. Get Google user info
    4. Look up user by google_id OR verified email (T034)
    5. Link Google identity if found by email (T035)
    6. Return error if no account found (T036)
    7. Create session and return tokens (T037)
    8. Log audit event (T038)

    T033: OAuth signin callback endpoint
    """
    import json
    import httpx

    # Extract client context
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Initialize services
    auth_service = AuthService(db, redis)

    try:
        # 1. Validate state token (CSRF protection)
        key = f"oauth:state:{state}"
        state_data_str = await redis.get(key)

        if not state_data_str:
            raise ValidationError("Invalid or expired OAuth state")

        state_data = json.loads(state_data_str)
        if state_data.get("flow") != "signin":
            raise ValidationError("Invalid OAuth flow - expected signin")

        # Delete state (one-time use)
        await redis.delete(key)

        # 2. Exchange code for tokens
        GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI.replace("/callback", "/signin/callback"),
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                raise ValidationError("Failed to exchange OAuth code")

            token_data = token_response.json()
            access_token_google = token_data["access_token"]

        # 3. Fetch user info from Google
        GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token_google}"},
            )

            if userinfo_response.status_code != 200:
                raise ValidationError("Failed to fetch user info from Google")

            google_user = userinfo_response.json()

        google_id = google_user["id"]
        google_email = google_user["email"]

        # 4. Look up user by google_id first, then by email (T034)
        user = await auth_service.user_repo.get_by_google_id(google_id)

        if not user:
            # Try to find by verified email
            user = await auth_service.user_repo.get_by_email(google_email)

            if user and user.email_verified:
                # 5. Link Google identity to existing account (T035)
                user.google_id = google_id
                await db.commit()
                await db.refresh(user)

                # Log Google identity linking (T038)
                await auth_service.log_auth_event(
                    event_type="GOOGLE_LINK",
                    result="success",
                    user_id=str(user.id),
                    ip_address=client_ip,
                    user_agent=user_agent,
                    metadata={"google_id": google_id},
                )
            elif not user:
                # 6. No account found - user needs to register first (T036)
                await auth_service.log_auth_event(
                    event_type="GOOGLE_SIGNIN",
                    result="failure",
                    email_attempted=google_email,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    metadata={"reason": "account_not_found", "google_id": google_id},
                )

                # Redirect to error page
                error_url = f"{settings.APP_URL}/signin?error=account_not_found"
                return Response(status_code=302, headers={"Location": error_url})

        # Check account status
        if not user.is_active:
            raise ValidationError("Account is disabled")

        # 7. Create session (T037)
        session_id = await auth_service.create_session(
            user_id=str(user.id),
            device_info=user_agent,
            ip_address=client_ip,
            remember_me=False,  # Default for OAuth
        )

        # Get user's primary workspace for JWT token
        workspace_member_repo = WorkspaceMemberRepository(db)
        user_workspaces = await workspace_member_repo.get_user_workspaces(str(user.id))
        primary_workspace_id = str(user_workspaces[0].workspace_id) if user_workspaces else None

        # Create tokens
        access_token_expires = 15 * 60  # 15 minutes

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "email_verified": user.email_verified,
                "workspace_id": primary_workspace_id,
            }
        )

        refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
                "type": "refresh",
                "session_id": session_id,
            },
            expires_delta=timedelta(days=7),
        )

        # Set HttpOnly Secure cookie (T037)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 60 * 60,
        )

        # 8. Log successful signin (T038)
        await auth_service.log_auth_event(
            event_type="GOOGLE_SIGNIN" if user.google_id == google_id else "LOGIN_SUCCESS",
            result="success",
            user_id=str(user.id),
            ip_address=client_ip,
            user_agent=user_agent,
            session_id=session_id,
            metadata={"google_id": google_id},
        )

        # Return response
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=access_token_expires,
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                avatar_url=getattr(user, 'avatar_url', None),
                email_verified=user.email_verified,
            ),
        )

    except Exception as e:
        # Log failed attempt
        await auth_service.log_auth_event(
            event_type="GOOGLE_SIGNIN",
            result="failure",
            ip_address=client_ip,
            user_agent=user_agent,
            metadata={"reason": str(e)},
        )
        raise

# ==========================================
# Phase 5: User Story 3 - Session Refresh
# ==========================================

@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Refresh access token using refresh token cookie",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Refresh access token using refresh token from HttpOnly cookie.

    Security features:
    - T045: Validates refresh token from HttpOnly cookie
    - T046: Token rotation - issues new refresh token on refresh
    - T047: Session validation from Redis
    - T048: Updates session last_activity timestamp
    - T049: Audit logging for TOKEN_REFRESH events
    - T050: Handles expired/invalid tokens (clears cookie, returns 401)

    Returns:
    - New JWT access token (15 min expiry)
    - New refresh token in HttpOnly cookie (token rotation)
    """

    # Extract client context
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Initialize auth service
    auth_service = AuthService(db, redis)

    try:
        # T045: Get refresh token from HttpOnly cookie
        refresh_token_str = request.cookies.get("refresh_token")
        if not refresh_token_str:
            raise AuthenticationError("No refresh token provided")

        # Verify refresh token
        payload = verify_token(refresh_token_str, expected_type="refresh")
        if not payload:
            # T050: Clear cookie on invalid token
            response.delete_cookie(key="refresh_token")
            raise AuthenticationError("Invalid or expired refresh token")

        user_id = payload.get("sub")
        session_id = payload.get("session_id")

        if not user_id or not session_id:
            response.delete_cookie(key="refresh_token")
            raise AuthenticationError("Invalid token payload")

        # T047: Validate session exists in Redis
        session_data = await auth_service.get_session(user_id, session_id)
        if not session_data:
            response.delete_cookie(key="refresh_token")
            raise AuthenticationError("Session not found or expired")

        # T048: Update session last_activity timestamp
        await auth_service.update_session_activity(user_id, session_id)

        # Get user from database
        user = await auth_service.user_repo.get(user_id)
        if not user or not user.is_active:
            response.delete_cookie(key="refresh_token")
            raise AuthenticationError("User not found or inactive")

        # Get user's primary workspace for JWT token
        workspace_member_repo = WorkspaceMemberRepository(db)
        user_workspaces = await workspace_member_repo.get_user_workspaces(str(user.id))
        primary_workspace_id = str(user_workspaces[0].workspace_id) if user_workspaces else None

        # Create new access token
        access_token_expires = 15 * 60  # 15 minutes in seconds
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "email_verified": user.email_verified,
                "workspace_id": primary_workspace_id,
            }
        )

        # T046: Token rotation - create new refresh token
        refresh_token_expires_days = 30 if session_data.get("remember_me") else 7
        new_refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
                "type": "refresh",
                "session_id": session_id,
            },
            expires_delta=timedelta(days=refresh_token_expires_days),
        )

        # Set new refresh token in HttpOnly cookie (token rotation)
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=refresh_token_expires_days * 24 * 60 * 60,
        )

        # T049: Log token refresh event
        await auth_service.log_auth_event(
            event_type="TOKEN_REFRESH",
            result="success",
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            session_id=session_id,
        )

        # Return new access token
        return RefreshResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=access_token_expires,
        )

    except AuthenticationError as e:
        # Log failed refresh attempt
        await auth_service.log_auth_event(
            event_type="TOKEN_REFRESH",
            result="failure",
            ip_address=client_ip,
            user_agent=user_agent,
            metadata={"reason": str(e)},
        )
        raise


# ==========================================
# Phase 6: User Story 4 - Logout
# ==========================================

@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout current session",
    description="End current user session and clear refresh token cookie",
    responses={
        200: {"description": "Logged out successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Logout current session.

    Functionality:
    - T057: Deletes session from Redis
    - T058: Clears refresh token cookie (Max-Age=0)
    - T059: Audit logging for LOGOUT events

    Returns:
    - Confirmation message
    - Clears HttpOnly refresh token cookie
    """

    # Extract client context
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Initialize auth service
    auth_service = AuthService(db, redis)

    user_id = None
    session_id = None

    try:
        # Get refresh token from cookie
        refresh_token_str = request.cookies.get("refresh_token")

        if refresh_token_str:
            # Try to extract user_id and session_id from token
            payload = verify_token(refresh_token_str, expected_type="refresh")
            if payload:
                user_id = payload.get("sub")
                session_id = payload.get("session_id")

                # T057: Delete session from Redis
                if user_id and session_id:
                    await auth_service.delete_session(user_id, session_id)

        # T058: Clear refresh token cookie (Max-Age=0)
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=True,
            samesite="strict",
        )

        # T059: Log logout event
        await auth_service.log_auth_event(
            event_type="LOGOUT",
            result="success",
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            session_id=session_id,
        )

        return LogoutResponse(message="Logged out successfully")

    except Exception as e:
        # Still clear cookie even if error occurs
        response.delete_cookie(key="refresh_token")

        # Log failed logout (shouldn't normally happen)
        await auth_service.log_auth_event(
            event_type="LOGOUT",
            result="failure",
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            metadata={"reason": str(e)},
        )

        # Return success anyway (logout should be idempotent)
        return LogoutResponse(message="Logged out successfully")


@router.post(
    "/logout/all",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout all devices",
    description="End all user sessions across all devices",
    responses={
        200: {"description": "Logged out from all devices"},
        401: {"description": "Not authenticated"},
    },
)
async def logout_all(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Logout all devices.

    Functionality:
    - T061: Deletes all sessions for user (KEYS + DEL pattern)
    - Clears refresh token cookie
    - Audit logging for LOGOUT_ALL events

    Returns:
    - Confirmation message with number of sessions deleted
    """

    # Extract client context
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Initialize auth service
    auth_service = AuthService(db, redis)

    user_id = None

    try:
        # Get refresh token from cookie
        refresh_token_str = request.cookies.get("refresh_token")

        if not refresh_token_str:
            raise AuthenticationError("No refresh token provided")

        # Extract user_id from token
        payload = verify_token(refresh_token_str, expected_type="refresh")
        if not payload:
            raise AuthenticationError("Invalid or expired refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        # T061: Delete all sessions for user
        deleted_count = await auth_service.delete_all_sessions(user_id)

        # Clear refresh token cookie
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=True,
            samesite="strict",
        )

        # Log logout all event
        await auth_service.log_auth_event(
            event_type="LOGOUT_ALL",
            result="success",
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            metadata={"sessions_deleted": deleted_count},
        )

        return LogoutResponse(
            message=f"Logged out from all devices ({deleted_count} sessions ended)"
        )

    except AuthenticationError as e:
        # Still clear cookie
        response.delete_cookie(key="refresh_token")

        # Log failed logout all
        await auth_service.log_auth_event(
            event_type="LOGOUT_ALL",
            result="failure",
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            metadata={"reason": str(e)},
        )

        raise


@router.get("/health", summary="Login API health check")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "login"}
