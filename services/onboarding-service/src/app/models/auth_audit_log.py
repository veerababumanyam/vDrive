"""AuthAuditLog model for tracking authentication events."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base


class AuthAuditLog(Base):
    """
    Security audit log for all authentication events.

    Tracks signin attempts, logouts, token refreshes, and account lockouts
    for security monitoring and compliance.
    """
    __tablename__ = "auth_audit_log"

    # Primary key
    id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Event details
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)

    # User context
    user_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    email_attempted: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Additional data
    event_metadata: Mapped[dict] = mapped_column(
        "metadata",  # Database column name
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "result IN ('success', 'failure')",
            name="auth_audit_log_result_check"
        ),
    )

    # Relationship (optional, for queries)
    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<AuthAuditLog(id={self.id}, event={self.event_type}, "
            f"result={self.result}, user_id={self.user_id})>"
        )
