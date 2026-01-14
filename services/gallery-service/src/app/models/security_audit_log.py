"""Security audit log model for tracking security events."""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.database import Base


class SecurityAuditLog(Base):
    """Security audit log for tracking gallery access and security events."""

    __tablename__ = "security_audit_log"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        server_default=text("gen_random_uuid()::text"),
    )

    # Foreign key (nullable to log events before gallery is identified)
    gallery_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("galleries.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Event details
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # link_access, password_attempt, pin_attempt, download, etc.
    result: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )  # success, failure, blocked
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Event metadata (JSONB for flexible storage)
    # Note: Using 'event_metadata' instead of 'metadata' to avoid SQLAlchemy reserved name
    event_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True,
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index("idx_security_audit_gallery_type", "gallery_id", "event_type"),
        Index("idx_security_audit_type_result", "event_type", "result"),
        Index("idx_security_audit_created", "created_at"),
    )

    def to_dict(self) -> dict:
        """Convert audit log to dictionary."""
        return {
            "id": self.id,
            "gallery_id": self.gallery_id,
            "event_type": self.event_type,
            "result": self.result,
            "message": self.message,
            "event_metadata": self.event_metadata,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
