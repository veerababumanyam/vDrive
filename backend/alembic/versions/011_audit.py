"""Create audit log table

Revision ID: 011_audit
Revises: 010_invitations
Create Date: 2025-01-01 00:10:00.000000

Tables:
- audit_logs: Event sourcing and audit trail
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "011_audit"
down_revision: Union[str, None] = "010_invitations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Audit logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True),
        # Actor
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_email", sa.String(255), nullable=True),  # Denormalized for historical record
        sa.Column("actor_type", sa.String(20), nullable=False, server_default="user"),
        # user, system, api_key, webhook
        # Event details
        sa.Column("event_type", sa.String(100), nullable=False),  # e.g., user.login, gallery.created, asset.deleted
        sa.Column("event_category", sa.String(50), nullable=False),  # auth, gallery, asset, billing, etc.
        sa.Column("description", sa.String(500), nullable=True),  # Human-readable description
        # Resource
        sa.Column("resource_type", sa.String(50), nullable=True),  # user, gallery, asset, etc.
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_name", sa.String(255), nullable=True),  # Denormalized for historical record
        # Changes (for update events)
        sa.Column("old_values", postgresql.JSONB(), nullable=True),
        sa.Column("new_values", postgresql.JSONB(), nullable=True),
        # Context
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("request_id", sa.String(36), nullable=True),  # Correlation ID
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Additional metadata
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        # Severity/importance
        sa.Column("severity", sa.String(20), nullable=False, server_default="info"),
        # debug, info, warning, error, critical
        # Flags
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default="false"),  # Contains sensitive data
        sa.Column("is_billable", sa.Boolean(), nullable=False, server_default="false"),  # Billable action
        # Timestamp
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Indexes for audit_logs
    # Primary query patterns: by workspace, by actor, by event type, by resource, by time range
    op.create_index("ix_audit_logs_workspace_id", "audit_logs", ["workspace_id"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_event_category", "audit_logs", ["event_category"])
    op.create_index("ix_audit_logs_resource_type_id", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_severity", "audit_logs", ["severity"])

    # Composite index for common query: workspace + time range
    op.create_index(
        "ix_audit_logs_workspace_created",
        "audit_logs",
        ["workspace_id", "created_at"]
    )

    # BRIN index for time-series queries (more efficient for large tables)
    op.execute("""
        CREATE INDEX ix_audit_logs_created_at_brin
        ON audit_logs
        USING brin (created_at)
        WITH (pages_per_range = 128)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_created_at_brin")
    op.drop_table("audit_logs")
