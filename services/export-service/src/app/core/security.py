"""
Security utilities for Export Service.

Provides JWT token validation for authentication.
"""

from typing import Any, Dict, Optional

from jose import JWTError, jwt

from src.app.core.config import settings


def verify_token(token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        Token payload dict if valid, None if invalid

    Example:
        payload = verify_token(token, expected_type="access")
        if payload:
            user_id = payload.get("sub")
    """
    try:
        # Decode JWT using secret key and algorithm
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Verify token type matches expected
        token_type = payload.get("type")
        if token_type != expected_type:
            return None

        return payload

    except JWTError:
        return None
