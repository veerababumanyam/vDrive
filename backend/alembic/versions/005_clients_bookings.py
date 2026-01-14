"""Create clients and bookings tables

Revision ID: 005_clients_bookings
Revises: 004_faces_people
Create Date: 2025-01-01 00:04:00.000000

Tables:
- clients: Client CRM records
- client_activity: Activity tracking for clients
- bookings: Photography session bookings
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_clients_bookings"
down_revision: Union[str, None] = "004_faces_people"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Clients table
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        # Contact info
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("secondary_email", sa.String(255), nullable=True),
        sa.Column("secondary_phone", sa.String(20), nullable=True),
        # Address
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        # Social/business
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("instagram", sa.String(100), nullable=True),
        # CRM fields
        sa.Column("source", sa.String(100), nullable=True),  # How they found us: referral, google, instagram, etc.
        sa.Column("referral_source", sa.String(200), nullable=True),  # Specific referrer name
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("notes", sa.Text(), nullable=True),
        # Preferences
        sa.Column("preferred_contact_method", sa.String(20), nullable=True),  # email, phone, text
        sa.Column("timezone", sa.String(50), nullable=True),
        sa.Column("locale", sa.String(10), nullable=True),
        # Stats (denormalized)
        sa.Column("total_bookings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_spent", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_galleries", sa.Integer(), nullable=False, server_default="0"),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),  # active, archived, blocked
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_reason", sa.String(500), nullable=True),
        # Associated user (if client has logged in)
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Timestamps
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("workspace_id", "email", name="uq_client_workspace_email"),
    )

    # Indexes for clients
    op.create_index("ix_clients_workspace_id", "clients", ["workspace_id"])
    op.create_index("ix_clients_email", "clients", ["email"])
    op.create_index("ix_clients_status", "clients", ["status"])
    op.create_index("ix_clients_tags", "clients", ["tags"], postgresql_using="gin")
    op.create_index("ix_clients_created_at", "clients", ["created_at"])

    # Add client_id FK to galleries
    op.create_foreign_key(
        "fk_galleries_client",
        "galleries", "clients",
        ["client_id"], ["id"],
        ondelete="SET NULL"
    )

    # Client activity table
    op.create_table(
        "client_activity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        # Activity details
        sa.Column("activity_type", sa.String(50), nullable=False),  # gallery_view, photo_download, selection_made, etc.
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),  # Activity-specific data
        # Related entities
        sa.Column("gallery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("galleries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=True),  # FK added after bookings table
        # Context
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("device_type", sa.String(50), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Indexes for client_activity
    op.create_index("ix_client_activity_workspace_id", "client_activity", ["workspace_id"])
    op.create_index("ix_client_activity_client_id", "client_activity", ["client_id"])
    op.create_index("ix_client_activity_type", "client_activity", ["activity_type"])
    op.create_index("ix_client_activity_created_at", "client_activity", ["created_at"])

    # Bookings table
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
        # Booking details
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("booking_type", sa.String(50), nullable=False),  # wedding, portrait, corporate, event, etc.
        # Schedule
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("all_day", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        # Location
        sa.Column("location_name", sa.String(255), nullable=True),
        sa.Column("location_address", sa.Text(), nullable=True),
        sa.Column("location_latitude", sa.Float(), nullable=True),
        sa.Column("location_longitude", sa.Float(), nullable=True),
        sa.Column("location_notes", sa.Text(), nullable=True),
        # Pricing
        sa.Column("package_name", sa.String(200), nullable=True),
        sa.Column("base_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("additional_fees", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("discount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("deposit_required", sa.Numeric(12, 2), nullable=True),
        sa.Column("deposit_paid", sa.Boolean(), nullable=False, server_default="false"),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="inquiry"),  # inquiry, pending, confirmed, completed, cancelled
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.String(500), nullable=True),
        # Contract
        sa.Column("contract_url", sa.String(2048), nullable=True),
        sa.Column("contract_signed_at", sa.DateTime(timezone=True), nullable=True),
        # Notes
        sa.Column("internal_notes", sa.Text(), nullable=True),  # Private notes for photographer
        sa.Column("client_notes", sa.Text(), nullable=True),  # Notes from client
        # Related
        sa.Column("gallery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("galleries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for bookings
    op.create_index("ix_bookings_workspace_id", "bookings", ["workspace_id"])
    op.create_index("ix_bookings_client_id", "bookings", ["client_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index("ix_bookings_start_datetime", "bookings", ["start_datetime"])
    op.create_index("ix_bookings_booking_type", "bookings", ["booking_type"])

    # Add booking_id FK to client_activity
    op.create_foreign_key(
        "fk_client_activity_booking",
        "client_activity", "bookings",
        ["booking_id"], ["id"],
        ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_client_activity_booking", "client_activity", type_="foreignkey")
    op.drop_table("bookings")
    op.drop_table("client_activity")
    op.drop_constraint("fk_galleries_client", "galleries", type_="foreignkey")
    op.drop_table("clients")
