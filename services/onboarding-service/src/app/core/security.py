"""
Security utilities for Onboarding Service.

Provides password hashing (Argon2id), JWT token management, and token generation.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHash, VerificationError
from jose import JWTError, jwt

from src.app.core.config import settings


# ===========================================
# Argon2id Password Hasher Configuration
# ===========================================
# OWASP recommended parameters for high-security applications
password_hasher = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
    hash_len=32,
    salt_len=16,
    type=Type.ID,  # Argon2id - hybrid of Argon2i and Argon2d
)


def hash_password(password: str) -> str:
    """
    Hash password using Argon2id.

    Args:
        password: Plain text password to hash

    Returns:
        Argon2id hash string (includes algorithm parameters, salt, and hash)

    Example:
        hashed = hash_password("SecureP@ss123!")
        # Returns: $argon2id$v=19$m=65536,t=3,p=4$...
    """
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against Argon2id hash.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored Argon2id hash

    Returns:
        True if password matches, False otherwise
    """
    try:
        password_hasher.verify(hashed_password, plain_password)
        return True
    except (VerificationError, InvalidHash):
        return False


def check_needs_rehash(hashed_password: str) -> bool:
    """
    Check if password hash needs to be updated.

    Returns True if hash was created with outdated parameters.
    Call after successful verification to update hashes with old parameters.

    Args:
        hashed_password: Stored Argon2id hash

    Returns:
        True if rehashing is recommended
    """
    return password_hasher.check_needs_rehash(hashed_password)


# ===========================================
# Token Generation
# ===========================================
def generate_verification_token() -> str:
    """
    Generate cryptographically secure verification token.

    Uses secrets.token_urlsafe for URL-safe base64 encoding.

    Returns:
        32-byte URL-safe token string (43 characters)
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """
    Hash token using SHA-256 for database storage.

    Tokens are hashed before storage to prevent token theft if database is compromised.

    Args:
        token: Plain text token to hash

    Returns:
        Hex-encoded SHA-256 hash (64 characters)
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def compare_tokens(token1: str, token2: str) -> bool:
    """
    Constant-time token comparison to prevent timing attacks.

    Args:
        token1: First token
        token2: Second token

    Returns:
        True if tokens match
    """
    return secrets.compare_digest(token1, token2)


def generate_oauth_state() -> str:
    """
    Generate secure OAuth state parameter.

    Prevents CSRF attacks during OAuth flow.

    Returns:
        32-byte URL-safe state string
    """
    return secrets.token_urlsafe(32)


# ===========================================
# JWT Token Management
# ===========================================
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload data (must include 'sub' for user ID)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT refresh token.

    Args:
        data: Payload data (must include 'sub' for user ID)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict, or None if invalid/expired

    Raises:
        JWTError: If token is malformed
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and check type.

    Args:
        token: JWT token string
        expected_type: Expected token type ('access' or 'refresh')

    Returns:
        Decoded payload if valid and correct type, None otherwise
    """
    payload = decode_token(token)
    if payload is None:
        return None

    # Verify token type
    token_type = payload.get("type")
    if token_type != expected_type:
        return None

    # Verify required claims
    if "sub" not in payload:
        return None

    return payload


# ===========================================
# Password Validation
# ===========================================
class PasswordValidator:
    """
    Password strength validator.

    Enforces:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """

    MIN_LENGTH = 8
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    @classmethod
    def validate(cls, password: str) -> Dict[str, Any]:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            Dict with 'valid' bool and 'errors' list
        """
        errors = []

        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters")

        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        if not any(c in cls.SPECIAL_CHARS for c in password):
            errors.append(f"Password must contain at least one special character ({cls.SPECIAL_CHARS})")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    @classmethod
    def is_valid(cls, password: str) -> bool:
        """Check if password meets strength requirements."""
        return cls.validate(password)["valid"]
