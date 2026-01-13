"""
Middleware for authentication, rate limiting, and error handling.
"""

from src.app.middleware.auth import get_current_user, get_optional_user
from src.app.middleware.error_handler import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    register_error_handlers,
)
from src.app.middleware.rate_limit import RateLimiter

__all__ = [
    "get_current_user",
    "get_optional_user",
    "RateLimiter",
    "register_error_handlers",
    "ValidationError",
    "AuthenticationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
]
