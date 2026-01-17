"""Service for security audit logging."""

from typing import Any, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.logging import logger
from src.app.models.security_audit_log import SecurityAuditLog


class SecurityAuditService:
    """Service for logging security events."""

    @staticmethod
    async def log_event(
        event_type: str,
        result: str,
        message: str,
        db: AsyncSession,
        gallery_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> None:
        """Log a security event to the audit log.

        Args:
            event_type: Type of event (link_access, password_attempt, pin_attempt, etc.)
            result: Result of event (success, failure, blocked)
            message: Human-readable message
            db: Database session
            gallery_id: Optional gallery UUID
            metadata: Optional additional metadata
            request: Optional FastAPI request for IP/user-agent extraction
        """
        # Extract request context
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        # Create audit log entry
        audit_log = SecurityAuditLog(
            gallery_id=gallery_id,
            event_type=event_type,
            result=result,
            message=message,
            event_metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(audit_log)
        await db.commit()

        # Also log to structured logs
        logger.info(
            "Security event logged",
            event_type=event_type,
            result=result,
            gallery_id=gallery_id,
            ip_address=ip_address,
        )

    @staticmethod
    async def log_link_access(
        link_id: str,
        gallery_id: str,
        result: str,
        db: AsyncSession,
        request: Optional[Request] = None,
        error: Optional[str] = None,
    ) -> None:
        """Log magic link access attempt.

        Args:
            link_id: Share link token
            gallery_id: Gallery UUID
            result: success, failure, blocked
            db: Database session
            request: Optional FastAPI request
            error: Optional error code if failed
        """
        message = f"Magic link access {result}"
        if error:
            message += f": {error}"

        await SecurityAuditService.log_event(
            event_type="link_access",
            result=result,
            message=message,
            db=db,
            gallery_id=gallery_id,
            metadata={"link_id": link_id, "error": error},
            request=request,
        )

    @staticmethod
    async def log_password_attempt(
        link_id: str,
        gallery_id: str,
        success: bool,
        db: AsyncSession,
        request: Optional[Request] = None,
    ) -> None:
        """Log gallery password verification attempt.

        Args:
            link_id: Share link token
            gallery_id: Gallery UUID
            success: Whether password was correct
            db: Database session
            request: Optional FastAPI request
        """
        result = "success" if success else "failure"
        message = f"Password verification {result}"

        await SecurityAuditService.log_event(
            event_type="password_attempt",
            result=result,
            message=message,
            db=db,
            gallery_id=gallery_id,
            metadata={"link_id": link_id},
            request=request,
        )

    @staticmethod
    async def log_pin_attempt(
        asset_id: str,
        gallery_id: str,
        success: bool,
        db: AsyncSession,
        request: Optional[Request] = None,
    ) -> None:
        """Log PIN verification attempt for private asset.

        Args:
            asset_id: Gallery asset UUID
            gallery_id: Gallery UUID
            success: Whether PIN was correct
            db: Database session
            request: Optional FastAPI request
        """
        result = "success" if success else "failure"
        message = f"PIN verification {result} for asset"

        await SecurityAuditService.log_event(
            event_type="pin_attempt",
            result=result,
            message=message,
            db=db,
            gallery_id=gallery_id,
            metadata={"asset_id": asset_id},
            request=request,
        )

    @staticmethod
    async def log_download(
        asset_id: str,
        gallery_id: str,
        db: AsyncSession,
        request: Optional[Request] = None,
    ) -> None:
        """Log asset download event.

        Args:
            asset_id: Gallery asset UUID
            gallery_id: Gallery UUID
            db: Database session
            request: Optional FastAPI request
        """
        await SecurityAuditService.log_event(
            event_type="download",
            result="success",
            message="Asset downloaded",
            db=db,
            gallery_id=gallery_id,
            metadata={"asset_id": asset_id},
            request=request,
        )
