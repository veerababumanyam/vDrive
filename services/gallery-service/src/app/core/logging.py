"""
Structured JSON logging for audit and debugging.
"""

import json
import logging
import sys
from datetime import datetime, timezone
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
            action: Action being performed (e.g., "gallery.create")
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

    def gallery_creation(
        self,
        user_id: str,
        workspace_id: str,
        gallery_id: str,
        gallery_name: str,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log gallery creation attempt."""
        self.log(
            action="gallery.create",
            status="success" if success else "failure",
            user_id=user_id,
            workspace_id=workspace_id,
            context={
                "gallery_id": gallery_id,
                "gallery_name": gallery_name,
                "error": error,
            },
        )

    def gallery_deletion(
        self,
        user_id: str,
        workspace_id: str,
        gallery_id: str,
        success: bool,
        photo_count: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """Log gallery deletion attempt."""
        self.log(
            action="gallery.delete",
            status="success" if success else "failure",
            user_id=user_id,
            workspace_id=workspace_id,
            context={
                "gallery_id": gallery_id,
                "photo_count": photo_count,
                "error": error,
            },
        )

    def photo_upload(
        self,
        user_id: str,
        workspace_id: str,
        gallery_id: str,
        photo_id: str,
        file_size_bytes: int,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log photo upload attempt."""
        self.log(
            action="photo.upload",
            status="success" if success else "failure",
            user_id=user_id,
            workspace_id=workspace_id,
            context={
                "gallery_id": gallery_id,
                "photo_id": photo_id,
                "file_size_bytes": file_size_bytes,
                "error": error,
            },
        )

    def photo_deletion(
        self,
        user_id: str,
        workspace_id: str,
        gallery_id: str,
        photo_id: str,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log photo deletion attempt."""
        self.log(
            action="photo.delete",
            status="success" if success else "failure",
            user_id=user_id,
            workspace_id=workspace_id,
            context={
                "gallery_id": gallery_id,
                "photo_id": photo_id,
                "error": error,
            },
        )

    def watermark_application(
        self,
        user_id: str,
        workspace_id: str,
        gallery_id: str,
        batch_id: str,
        photo_count: int,
        success: bool,
        watermark_type: str = "text",
        error: Optional[str] = None,
    ) -> None:
        """Log watermark application attempt."""
        self.log(
            action="watermark.apply",
            status="success" if success else "failure",
            user_id=user_id,
            workspace_id=workspace_id,
            context={
                "gallery_id": gallery_id,
                "batch_id": batch_id,
                "photo_count": photo_count,
                "watermark_type": watermark_type,
                "error": error,
            },
        )

    def watermark_removal(
        self,
        user_id: str,
        workspace_id: str,
        gallery_id: str,
        photo_count: int,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log watermark removal attempt."""
        self.log(
            action="watermark.remove",
            status="success" if success else "failure",
            user_id=user_id,
            workspace_id=workspace_id,
            context={
                "gallery_id": gallery_id,
                "photo_count": photo_count,
                "error": error,
            },
        )

    def storage_access(
        self,
        user_id: str,
        workspace_id: str,
        action: str,
        object_key: str,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log storage access (R2/S3) operations."""
        self.log(
            action=f"storage.{action}",
            status="success" if success else "failure",
            user_id=user_id,
            workspace_id=workspace_id,
            context={
                "object_key": object_key,
                "error": error,
            },
        )

    def rate_limit_exceeded(
        self,
        endpoint: str,
        workspace_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Log rate limit violation."""
        self.log(
            action="security.rate_limit_exceeded",
            status="denied",
            user_id=user_id,
            workspace_id=workspace_id,
            context={
                "endpoint": endpoint,
            },
        )


# Global audit logger instance
audit_logger = AuditLogger()
