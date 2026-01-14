"""Create webhooks tables

Revision ID: 008_webhooks
Revises: 007_notifications
Create Date: 2025-01-01 00:07:00.000000

Tables:
- webhook_subscriptions: Registered webhook endpoints
- webhook_deliveries: Webhook delivery history
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "008_webhooks"
down_revision: Union[str, None] = "007_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Webhook subscriptions table
    op.create_table(
        "webhook_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        # Webhook configuration
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("events", postgresql.ARRAY(sa.String()), nullable=False),  # e.g., ['gallery.published', 'asset.uploaded']
        # Security
        sa.Column("secret", sa.String(255), nullable=False),  # For HMAC signature verification
        sa.Column("secret_hash", sa.String(255), nullable=False),  # Hashed version for storage
        # Headers
        sa.Column("headers", postgresql.JSONB(), nullable=False, server_default="{}"),  # Custom headers to include
        # Content type
        sa.Column("content_type", sa.String(50), nullable=False, server_default="application/json"),
        # Retry configuration
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("initial_delay_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("backoff_multiplier", sa.Float(), nullable=False, server_default="2"),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),  # active, paused, disabled
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_reason", sa.String(500), nullable=True),
        # Stats (denormalized)
        sa.Column("total_deliveries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_deliveries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_deliveries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        # Auto-disable after failures
        sa.Column("auto_disable_threshold", sa.Integer(), nullable=False, server_default="10"),
        # Last activity
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        # Created by
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for webhook_subscriptions
    op.create_index("ix_webhook_subscriptions_workspace_id", "webhook_subscriptions", ["workspace_id"])
    op.create_index("ix_webhook_subscriptions_status", "webhook_subscriptions", ["status"])
    op.create_index("ix_webhook_subscriptions_events", "webhook_subscriptions", ["events"], postgresql_using="gin")

    # Webhook deliveries table
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("webhook_subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        # Event details
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),  # Unique ID for this event
        # Request
        sa.Column("request_url", sa.String(2048), nullable=False),
        sa.Column("request_headers", postgresql.JSONB(), nullable=False),
        sa.Column("request_body", postgresql.JSONB(), nullable=False),
        # Response
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("response_headers", postgresql.JSONB(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),  # Truncated to 64KB
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        # pending, success, failed
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_type", sa.String(50), nullable=True),  # timeout, connection_error, http_error
        # Retry tracking
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="6"),  # 1 initial + 5 retries
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        # Related entity (for filtering)
        sa.Column("related_entity_type", sa.String(50), nullable=True),  # gallery, asset, client, etc.
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Timestamps
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Indexes for webhook_deliveries
    op.create_index("ix_webhook_deliveries_webhook_subscription_id", "webhook_deliveries", ["webhook_subscription_id"])
    op.create_index("ix_webhook_deliveries_workspace_id", "webhook_deliveries", ["workspace_id"])
    op.create_index("ix_webhook_deliveries_event_type", "webhook_deliveries", ["event_type"])
    op.create_index("ix_webhook_deliveries_status", "webhook_deliveries", ["status"])
    op.create_index("ix_webhook_deliveries_event_id", "webhook_deliveries", ["event_id"])
    op.create_index("ix_webhook_deliveries_next_retry_at", "webhook_deliveries", ["next_retry_at"])
    op.create_index("ix_webhook_deliveries_created_at", "webhook_deliveries", ["created_at"])


def downgrade() -> None:
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_subscriptions")
