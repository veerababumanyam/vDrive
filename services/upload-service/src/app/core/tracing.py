"""Request tracing with correlation IDs."""

import uuid
from contextvars import ContextVar
from typing import Optional

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store request ID across async calls
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

logger = structlog.get_logger()


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_ctx.get()


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to all requests.

    Generates or extracts X-Request-ID header and adds it to:
    - Response headers
    - Structured logging context
    - Context variable for access in route handlers
    """

    async def dispatch(self, request: Request, call_next):
        """Process request with tracing."""
        # Extract or generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Store in context variable
        request_id_ctx.set(request_id)

        # Bind to structured logging context
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

        try:
            # Process request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            )

            return response

        except Exception as e:
            # Log error with request ID
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                exc_info=True,
            )
            raise

        finally:
            # Clear context
            structlog.contextvars.clear_contextvars()
            request_id_ctx.set(None)
