"""
Authentication middleware for JWT token validation.

Provides FastAPI dependencies for extracting and validating user from requests.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.app.core.security import verify_token

# HTTP Bearer scheme for extracting JWT from Authorization header
oauth2_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    """
    Authenticated user context.

    Contains user information extracted from JWT token.
    """

    def __init__(
        self,
        user_id: str,
        email: str,
        workspace_id: Optional[str] = None,
        email_verified: bool = False,
    ):
        self.user_id = user_id
        self.email = email
        self.workspace_id = workspace_id
        self.email_verified = email_verified

    @property
    def id(self) -> str:
        """Alias for user_id."""
        return self.user_id


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
) -> CurrentUser:
    """
    FastAPI dependency to get current authenticated user.

    Extracts and validates JWT from Authorization header.

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        CurrentUser with user information

    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "AuthenticationRequired",
                "message": "Authentication required",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token(token, expected_type="access")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "InvalidToken",
                "message": "Invalid or expired authentication token",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user info from token
    user_id = payload.get("sub")
    email = payload.get("email")
    workspace_id = payload.get("workspace_id")
    email_verified = payload.get("email_verified", False)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "InvalidToken",
                "message": "Invalid token payload",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(
        user_id=user_id,
        email=email,
        workspace_id=workspace_id,
        email_verified=email_verified,
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
) -> Optional[CurrentUser]:
    """
    FastAPI dependency to optionally get current user.

    Returns None if no valid token is provided instead of raising.

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        CurrentUser if valid token, None otherwise
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def get_verified_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    FastAPI dependency to get current user with verified email.

    Args:
        current_user: Current authenticated user

    Returns:
        CurrentUser if email is verified

    Raises:
        HTTPException: 403 if email is not verified
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "EmailNotVerified",
                "message": "Please verify your email address before proceeding",
            },
        )
    return current_user
