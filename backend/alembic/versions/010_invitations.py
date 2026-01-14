"""Create invitations tables

Revision ID: 010_invitations
Revises: 009_albums
Create Date: 2025-01-01 00:09:00.000000

Tables:
- invitations: Event invitations (save the dates, etc.)
- invitation_guests: Guest list for invitations
- invitation_rsvps: RSVP responses
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "010_invitations"
down_revision: Union[str, None] = "009_albums"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Invitations table
    op.create_table(
        "invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
        # Event details
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False, server_default="wedding"),
        # wedding, corporate, birthday, anniversary, other
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        # Venue
        sa.Column("venue_name", sa.String(255), nullable=True),
        sa.Column("venue_address", sa.Text(), nullable=True),
        sa.Column("venue_map_url", sa.String(2048), nullable=True),
        sa.Column("venue_latitude", sa.Float(), nullable=True),
        sa.Column("venue_longitude", sa.Float(), nullable=True),
        # Content
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_image_url", sa.String(2048), nullable=True),
        sa.Column("cover_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="SET NULL"), nullable=True),
        # Template/design
        sa.Column("template_id", sa.String(100), nullable=True),
        sa.Column("custom_styles", postgresql.JSONB(), nullable=False, server_default="{}"),
        # RSVP settings
        sa.Column("rsvp_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("rsvp_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("allow_plus_ones", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_plus_ones", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("dietary_options", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("custom_questions", postgresql.JSONB(), nullable=False, server_default="[]"),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        # draft, sent, cancelled
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.String(500), nullable=True),
        # Stats (denormalized)
        sa.Column("guest_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rsvp_attending", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rsvp_declined", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rsvp_pending", sa.Integer(), nullable=False, server_default="0"),
        # Created by
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for invitations
    op.create_index("ix_invitations_workspace_id", "invitations", ["workspace_id"])
    op.create_index("ix_invitations_client_id", "invitations", ["client_id"])
    op.create_index("ix_invitations_event_date", "invitations", ["event_date"])
    op.create_index("ix_invitations_status", "invitations", ["status"])

    # Invitation guests table
    op.create_table(
        "invitation_guests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("invitation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invitations.id", ondelete="CASCADE"), nullable=False),
        # Guest info
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("group_name", sa.String(100), nullable=True),  # Family, Friends, etc.
        # RSVP tracking
        sa.Column("rsvp_token", sa.String(64), nullable=False, unique=True),
        sa.Column("rsvp_status", sa.String(20), nullable=False, server_default="pending"),
        # pending, attending, declined, maybe
        sa.Column("plus_ones", sa.Integer(), nullable=True),
        sa.Column("plus_one_names", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("dietary_requirements", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("custom_answers", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("message", sa.Text(), nullable=True),  # Message from guest
        # Status
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_count", sa.Integer(), nullable=False, server_default="0"),
        # Notes (private)
        sa.Column("notes", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("invitation_id", "email", name="uq_invitation_guest_email"),
    )

    # Indexes for invitation_guests
    op.create_index("ix_invitation_guests_invitation_id", "invitation_guests", ["invitation_id"])
    op.create_index("ix_invitation_guests_email", "invitation_guests", ["email"])
    op.create_index("ix_invitation_guests_rsvp_token", "invitation_guests", ["rsvp_token"])
    op.create_index("ix_invitation_guests_rsvp_status", "invitation_guests", ["rsvp_status"])


def downgrade() -> None:
    op.drop_table("invitation_guests")
    op.drop_table("invitations")
