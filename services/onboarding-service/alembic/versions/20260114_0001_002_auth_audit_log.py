"""Add auth_audit_log table for authentication event tracking

Revision ID: 002
Revises: 001
Create Date: 2026-01-14 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Create auth_audit_log table
    op.create_table(
        "auth_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email_attempted", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),  # IPv6 max length
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("result", sa.String(20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("result IN ('success', 'failure')", name="auth_audit_log_result_check"),
    )

    # Create indexes for common queries
    op.create_index("idx_auth_audit_user_id", "auth_audit_log", ["user_id"])
    op.create_index("idx_auth_audit_timestamp", "auth_audit_log", [sa.text("timestamp DESC")])
    op.create_index("idx_auth_audit_event_type", "auth_audit_log", ["event_type"])
    op.create_index("idx_auth_audit_ip", "auth_audit_log", ["ip_address"])


def downgrade() -> None:
    """Revert migration changes."""
    op.drop_index("idx_auth_audit_ip", table_name="auth_audit_log")
    op.drop_index("idx_auth_audit_event_type", table_name="auth_audit_log")
    op.drop_index("idx_auth_audit_timestamp", table_name="auth_audit_log")
    op.drop_index("idx_auth_audit_user_id", table_name="auth_audit_log")
    op.drop_table("auth_audit_log")
