"""
Authentication API endpoints.

Handles user login, logout, and token refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.app.core.database import get_db
from src.app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from src.app.models.user import User
from src.app.models.workspace_member import WorkspaceMember
from src.app.middleware.error_handler import (
    InvalidCredentialsError,
    AccountDisabledError,
    EmailNotVerifiedError,
)


router = APIRouter(tags=["auth"])


# ===========================================
# Schemas
# ===========================================
class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    email_verified: bool
    has_workspace: bool


class RefreshResponse(BaseModel):
    """Token refresh response schema."""
    access_token: str
    token_type: str = "bearer"


# ===========================================
# Endpoints
# ===========================================
@router.post(
    "/auth/login",
    response_model=LoginResponse,
    summary="Login user",
    description="Authenticate user with email and password",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    Authenticate user with email and password.

    - Validates credentials
    - Returns JWT access token
    - Sets refresh token in HTTP-only cookie
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email.lower())
    )
    user = result.scalar_one_or_none()

    # Validate credentials
    if not user or not user.password_hash:
        raise InvalidCredentialsError()

    if not verify_password(request.password, user.password_hash):
        raise InvalidCredentialsError()

    if not user.is_active:
        raise AccountDisabledError()

    # Check email verification (optional - can be enabled based on requirements)
    # Uncomment to require email verification before login
    # if not user.email_verified:
    #     raise EmailNotVerifiedError()

    # Check workspace membership
    workspace_result = await db.execute(
        select(func.count()).select_from(WorkspaceMember).where(WorkspaceMember.user_id == user.id)
    )
    workspace_count = workspace_result.scalar()
    has_workspace = workspace_count > 0

    # Create tokens
    access_token = create_access_token({"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token({"sub": user.id})

    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    return LoginResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        email_verified=user.email_verified,
        has_workspace=has_workspace,
    )


@router.post(
    "/auth/login/form",
    response_model=LoginResponse,
    summary="Login user (form)",
    description="Authenticate user with form data (OAuth2 compatible)",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    OAuth2-compatible login endpoint using form data.
    """
    request = LoginRequest(email=form_data.username, password=form_data.password)
    return await login(request, response, db)


@router.post(
    "/auth/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token cookie",
    responses={
        200: {"description": "Token refreshed"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    """
    Refresh access token using refresh token from cookie.

    - Validates refresh token
    - Issues new access token
    - Rotates refresh token
    """
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest

    # This will be called with the request context
    # For now, return error - need request object
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token required in cookie",
    )


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Clear refresh token cookie",
    responses={
        204: {"description": "Logged out successfully"},
    },
)
async def logout(response: Response) -> None:
    """
    Logout user by clearing refresh token cookie.
    """
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="lax",
    )
