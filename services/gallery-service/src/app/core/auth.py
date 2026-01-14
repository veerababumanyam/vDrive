"""JWT authentication and Magic Link verification"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from src.app.core.config import settings

oauth2_scheme = HTTPBearer()


class CurrentUser(BaseModel):
    """Current authenticated user context."""

    user_id: str
    email: str
    workspace_id: Optional[str] = None
    email_verified: bool = False


def verify_token(token: str, expected_type: str = "access") -> dict:
    """
    Verify JWT token and return payload.

    Args:
        token: JWT token string
        expected_type: Expected token type (access, refresh)

    Returns:
        Token payload dict

    Raises:
        HTTPException: If token is invalid
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
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> CurrentUser:
    """
    FastAPI dependency to get current authenticated user.

    Usage:
        @router.get("/staff/endpoint")
        async def endpoint(current_user: CurrentUser = Depends(get_current_user)):
            ...
    """
    token = credentials.credentials
    payload = verify_token(token, expected_type="access")

    return CurrentUser(
        user_id=payload["sub"],
        email=payload["email"],
        workspace_id=payload.get("workspace_id"),
        email_verified=payload.get("email_verified", False),
    )


def create_gallery_access_token(
    gallery_id: str,
    link_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT token for gallery access via magic link.

    Args:
        gallery_id: Gallery UUID
        link_id: Share link token
        expires_delta: Optional expiration time delta (default: 24 hours)

    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    expire = datetime.utcnow() + expires_delta

    payload = {
        "type": "gallery_access",
        "gallery_id": gallery_id,
        "link_id": link_id,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token


def extract_magic_link_token(link_id: str) -> str:
    """
    Extract and validate Magic Link token from link_id.

    Args:
        link_id: Magic Link ID from URL

    Returns:
        Validated link_id

    Raises:
        HTTPException: If link_id is invalid format
    """
    if not link_id or len(link_id) < 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Magic Link format",
        )

    return link_id
