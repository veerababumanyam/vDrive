"""
Centralized error handling for consistent API responses.

Provides custom exceptions and exception handlers for FastAPI.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


# ===========================================
# Custom Exception Classes
# ===========================================
class ServiceError(Exception):
    """Base exception for service errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "ServiceError",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ValidationError(ServiceError):
    """Raised for validation failures."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            error_code="ValidationError",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class AuthenticationError(ServiceError):
    """Raised for authentication failures."""

    def __init__(self, message: str = "Authentication required", error_code: str = "AuthenticationError"):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(ServiceError):
    """Raised for authorization failures."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code="AuthorizationError",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundError(ServiceError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            error_code="NotFoundError",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(ServiceError):
    """Raised for resource conflicts."""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            error_code="ConflictError",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class RateLimitError(ServiceError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
    ):
        super().__init__(
            message=message,
            error_code="RateLimitError",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=[{"retry_after": retry_after}],
        )
        self.retry_after = retry_after


class ExternalServiceError(ServiceError):
    """Raised when an external service fails."""

    def __init__(self, message: str = "External service unavailable"):
        super().__init__(
            message=message,
            error_code="ExternalServiceError",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class ExportError(ServiceError):
    """Raised when export job fails."""

    def __init__(self, message: str = "Export job failed"):
        super().__init__(
            message=message,
            error_code="ExportError",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class StorageError(ServiceError):
    """Raised when storage operations fail."""

    def __init__(self, message: str = "Storage operation failed"):
        super().__init__(
            message=message,
            error_code="StorageError",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ===========================================
# Exception Handlers
# ===========================================
def create_error_response(
    error_code: str,
    message: str,
    details: Optional[List[Dict[str, Any]]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create consistent error response format.

    Args:
        error_code: Error type code
        message: Human-readable error message
        details: Optional list of detailed errors
        request_id: Optional request ID for tracking

    Returns:
        Error response dictionary
    """
    response = {
        "error": error_code,
        "message": message,
    }
    if details:
        response["details"] = details
    if request_id:
        response["request_id"] = request_id
    return response


async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    """Handle custom service errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        ),
        headers={"Retry-After": str(exc.retry_after)} if isinstance(exc, RateLimitError) else None,
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle FastAPI validation errors."""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        details.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            error_code="ValidationError",
            message="Request validation failed",
            details=details,
        ),
    )


async def pydantic_error_handler(
    request: Request,
    exc: PydanticValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        details.append({
            "field": field,
            "message": error["msg"],
        })

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            error_code="ValidationError",
            message="Data validation failed",
            details=details,
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException to ensure consistent error format.

    Converts HTTPException.detail (which can be string or dict) to our standard format.
    """
    # If detail is already a dict with error/message, use it
    if isinstance(exc.detail, dict):
        error_code = exc.detail.get("error", "UnknownError")
        message = exc.detail.get("message", str(exc.detail))
        details = exc.detail.get("details")
    else:
        # detail is a string - create standard format
        error_code = "UnknownError"
        message = str(exc.detail) if exc.detail else "An error occurred"
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=error_code,
            message=message,
            details=details,
        ),
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    # Log the full error with structured logging
    logger.error(
        "Unhandled exception",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "path": str(request.url.path),
            "method": request.method,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            error_code="InternalError",
            message="An unexpected error occurred. Please try again later.",
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    """
    Register all error handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Register custom exceptions first (most specific)
    app.add_exception_handler(ServiceError, service_error_handler)

    # Register FastAPI built-in exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_error_handler)

    # Generic exception handler (catch-all, least specific)
    app.add_exception_handler(Exception, generic_error_handler)
