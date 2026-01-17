"""
Structured JSON logging for audit and debugging.
"""

import logging
import sys
from typing import Any, Dict, Optional
from uuid import uuid4

import structlog

from src.app.core.config import settings


def configure_logging() -> None:
    """
    Configure structured logging with JSON output.

    Sets up structlog with processors for:
    - Timestamp injection
    - Log level formatting
    - JSON serialization
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.DEBUG else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class AuditLogger:
    """
    Audit logger for security-relevant events.

    Logs to structured format with consistent fields:
    - request_id
    - user_id
    - workspace_id
    - action
    - status
    - timestamp
    - context
    """

    def __init__(self):
        self.logger = get_logger("audit")

    def log(
        self,
        action: str,
        status: str,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an audit event.

        Args:
            action: Action being performed (e.g., "export.create")
            status: Status of action ("success", "failure", "denied")
            user_id: User performing action
            workspace_id: Workspace context
            request_id: Request correlation ID
            context: Additional context data
        """
        self.logger.info(
            action,
            action=action,
            status=status,
            user_id=user_id,
            workspace_id=workspace_id,
            request_id=request_id or str(uuid4()),
            context=context or {},
            audit=True,
        )

    def export_created(
        self,
        user_id: str,
        workspace_id: str,
        export_job_id: str,
        export_type: str,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log export job creation."""
        self.log(
            action="export.create",
            status="success" if success else "failure",
            user_id=user_id,
            workspace_id=workspace_id,
            context={
                "export_job_id": export_job_id,
                "export_type": export_type,
                "error": error,
            },
        )

    def export_completed(
        self,
        user_id: str,
        workspace_id: str,
        export_job_id: str,
        total_assets: int,
        file_size: int,
        duration_seconds: float,
    ) -> None:
        """Log export job completion."""
        self.log(
            action="export.complete",
            status="success",
            user_id=user_id,
            workspace_id=workspace_id,
            context={
                "export_job_id": export_job_id,
                "total_assets": total_assets,
                "file_size": file_size,
                "duration_seconds": duration_seconds,
            },
        )

    def export_failed(
        self,
        user_id: str,
        workspace_id: str,
        export_job_id: str,
        error: str,
    ) -> None:
        """Log export job failure."""
        self.log(
            action="export.failed",
            status="failure",
            user_id=user_id,
            workspace_id=workspace_id,
            context={
                "export_job_id": export_job_id,
                "error": error,
            },
        )

    def rate_limit_exceeded(
        self,
        endpoint: str,
        ip_address: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Log rate limit violation."""
        self.log(
            action="security.rate_limit_exceeded",
            status="denied",
            user_id=user_id,
            context={
                "endpoint": endpoint,
                "ip_address": ip_address,
            },
        )


# Global audit logger instance
audit_logger = AuditLogger()
