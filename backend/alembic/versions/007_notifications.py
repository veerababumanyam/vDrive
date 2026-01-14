"""Create notifications tables

Revision ID: 007_notifications
Revises: 006_billing
Create Date: 2025-01-01 00:06:00.000000

Tables:
- notification_preferences: User notification settings
- notification_logs: Sent notification history
- push_tokens: Device push notification tokens
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007_notifications"
down_revision: Union[str, None] = "006_billing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Notification preferences table
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        # Email notifications
        sa.Column("email_gallery_viewed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_selection_complete", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_payment_received", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_new_booking", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_booking_reminder", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_weekly_digest", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_marketing", sa.Boolean(), nullable=False, server_default="false"),
        # Push notifications
        sa.Column("push_gallery_viewed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("push_selection_complete", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("push_payment_received", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("push_new_booking", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("push_booking_reminder", sa.Boolean(), nullable=False, server_default="true"),
        # In-app notifications
        sa.Column("in_app_gallery_viewed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("in_app_selection_complete", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("in_app_payment_received", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("in_app_new_booking", sa.Boolean(), nullable=False, server_default="true"),
        # Quiet hours
        sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("quiet_hours_start", sa.Time(), nullable=True),  # e.g., 22:00
        sa.Column("quiet_hours_end", sa.Time(), nullable=True),  # e.g., 08:00
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        # Unsubscribe token (for one-click unsubscribe)
        sa.Column("unsubscribe_token", sa.String(64), nullable=False, unique=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for notification_preferences
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"])
    op.create_index("ix_notification_preferences_unsubscribe_token", "notification_preferences", ["unsubscribe_token"])

    # Notification logs table
    op.create_table(
        "notification_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Notification details
        sa.Column("channel", sa.String(20), nullable=False),  # email, push, in_app
        sa.Column("notification_type", sa.String(50), nullable=False),  # gallery_invite, selection_reminder, etc.
        sa.Column("template_id", sa.String(100), nullable=True),
        # Recipient
        sa.Column("recipient_email", sa.String(255), nullable=True),
        sa.Column("recipient_name", sa.String(200), nullable=True),
        sa.Column("recipient_device_token", sa.String(500), nullable=True),
        # Content
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("body_preview", sa.String(500), nullable=True),
        sa.Column("data", postgresql.JSONB(), nullable=True),  # Template variables
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        # pending, sent, delivered, failed, bounced, complained
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),
        # External tracking
        sa.Column("external_id", sa.String(100), nullable=True),  # SendGrid message ID, etc.
        # Delivery tracking
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bounced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("complained_at", sa.DateTime(timezone=True), nullable=True),
        # Related entities
        sa.Column("gallery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("galleries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
        # Scheduling
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Indexes for notification_logs
    op.create_index("ix_notification_logs_workspace_id", "notification_logs", ["workspace_id"])
    op.create_index("ix_notification_logs_user_id", "notification_logs", ["user_id"])
    op.create_index("ix_notification_logs_channel", "notification_logs", ["channel"])
    op.create_index("ix_notification_logs_status", "notification_logs", ["status"])
    op.create_index("ix_notification_logs_notification_type", "notification_logs", ["notification_type"])
    op.create_index("ix_notification_logs_created_at", "notification_logs", ["created_at"])
    op.create_index("ix_notification_logs_external_id", "notification_logs", ["external_id"])

    # Push tokens table
    op.create_table(
        "push_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        # Token details
        sa.Column("token", sa.String(500), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),  # ios, android, web
        sa.Column("device_name", sa.String(200), nullable=True),
        sa.Column("device_model", sa.String(100), nullable=True),
        sa.Column("app_version", sa.String(50), nullable=True),
        # Status
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_reason", sa.String(500), nullable=True),
        # Timestamps
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("user_id", "token", name="uq_push_token_user_token"),
    )

    # Indexes for push_tokens
    op.create_index("ix_push_tokens_user_id", "push_tokens", ["user_id"])
    op.create_index("ix_push_tokens_platform", "push_tokens", ["platform"])
    op.create_index("ix_push_tokens_is_active", "push_tokens", ["is_active"])


def downgrade() -> None:
    op.drop_table("push_tokens")
    op.drop_table("notification_logs")
    op.drop_table("notification_preferences")
