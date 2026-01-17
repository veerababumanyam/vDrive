"""
JWT authentication for Upload Service.

Provides token verification and user extraction from JWTs.
"""

from typing import Optional

import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from .config import settings

logger = structlog.get_logger()

oauth2_scheme = HTTPBearer()


class CurrentUser(BaseModel):
    """Current authenticated user."""

    user_id: str
    email: str
    workspace_id: Optional[str] = None
    email_verified: bool = False


def verify_token(token: str, expected_type: str = "access") -> dict:
    """
    Verify JWT token and return payload.

    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        Token payload dict

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Verify token type
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type: expected {expected_type}, got {token_type}",
            )

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> CurrentUser:
    """
    FastAPI dependency to get current authenticated user.

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        CurrentUser instance

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    payload = verify_token(token, expected_type="access")

    return CurrentUser(
        user_id=payload["sub"],
        email=payload.get("email", ""),
        workspace_id=payload.get("workspace_id"),
        email_verified=payload.get("email_verified", False),
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[CurrentUser]:
    """
    FastAPI dependency for optional authentication.

    Returns CurrentUser if token is valid, None otherwise.
    Does not raise exceptions for missing/invalid tokens.
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token, expected_type="access")

        return CurrentUser(
            user_id=payload["sub"],
            email=payload.get("email", ""),
            workspace_id=payload.get("workspace_id"),
            email_verified=payload.get("email_verified", False),
        )
    except HTTPException:
        return None
