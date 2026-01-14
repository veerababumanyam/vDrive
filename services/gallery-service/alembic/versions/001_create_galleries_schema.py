"""Create galleries schema with 7 tables

Revision ID: 001
Revises:
Create Date: 2026-01-14

Tables created:
- galleries: Core gallery containers with workspace isolation
- sub_galleries: First-class sections within galleries
- share_links: Magic Links with QR configuration
- gallery_assets: Junction table linking assets to galleries
- visitors: Lead capture records
- gallery_visitors: Access log for analytics
- security_audit_log: Security events tracking
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all gallery-service tables."""

    # ===========================================
    # Table 1: galleries
    # ===========================================
    op.create_table(
        "galleries",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        # Multi-tenancy
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Basic info
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("client_name", sa.String(200), nullable=True),
        sa.Column("shoot_date", sa.Date(), nullable=True),
        # Status and lifecycle
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
            index=True,
        ),  # draft, published, archived
        # Cover image
        sa.Column(
            "cover_asset_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),  # FK added later (circular)
        # Settings
        sa.Column("password_protected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("pin_protected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "email_registration_required",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "download_policy",
            sa.String(20),
            nullable=False,
            server_default="view_only",
        ),  # view_only, web_only, watermarked_only, original_allowed
        sa.Column(
            "layout_style",
            sa.String(20),
            nullable=False,
            server_default="tab",
        ),  # tab, continuous_scroll
        sa.Column("theme", sa.String(20), nullable=True),  # dark, light, auto
        # Denormalized stats (updated via triggers)
        sa.Column("photo_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("video_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("favorites_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        # Branding
        sa.Column("primary_color", sa.String(7), nullable=True),  # hex color
        sa.Column("secondary_color", sa.String(7), nullable=True),
        # Audit fields
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Indexes for galleries
    op.create_index("ix_galleries_workspace_id", "galleries", ["workspace_id"])
    op.create_index("ix_galleries_status", "galleries", ["status"])
    op.create_index("ix_galleries_created_at", "galleries", ["created_at"])
    op.create_index(
        "ix_galleries_workspace_created",
        "galleries",
        ["workspace_id", "created_at"],
    )

    # ===========================================
    # Table 2: sub_galleries
    # ===========================================
    op.create_table(
        "sub_galleries",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        # Parent gallery
        sa.Column(
            "gallery_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("galleries.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Basic info
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default="true"),
        # Cover image
        sa.Column(
            "cover_asset_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),  # FK added later
        # Denormalized count
        sa.Column("photo_count", sa.Integer(), nullable=False, server_default="0"),
        # Audit fields
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Indexes for sub_galleries
    op.create_index("ix_sub_galleries_gallery_id", "sub_galleries", ["gallery_id"])
    op.create_index(
        "ix_sub_galleries_gallery_sort",
        "sub_galleries",
        ["gallery_id", "sort_order"],
    )

    # ===========================================
    # Table 3: share_links (Magic Links)
    # ===========================================
    op.create_table(
        "share_links",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        # Link ID (URL token - different from PK)
        sa.Column("link_id", sa.String(64), nullable=False, unique=True, index=True),
        # Parent gallery
        sa.Column(
            "gallery_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("galleries.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Metadata
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column(
            "target_type",
            sa.String(20),
            nullable=False,
            server_default="gallery",
        ),  # gallery, sub_gallery, photo
        # Status and expiration
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="active",
            index=True,
        ),  # active, expired, revoked
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_accesses", sa.Integer(), nullable=True),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        # Policies
        sa.Column("password_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column(
            "email_registration_required",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "allowed_actions",
            postgresql.ARRAY(sa.String(20)),
            nullable=False,
            server_default="{}",
        ),
        # view, favorite, select, comment, download
        sa.Column(
            "download_variant",
            sa.String(20),
            nullable=True,
        ),  # web, watermarked, original
        # QR configuration
        sa.Column("qr_size", sa.Integer(), nullable=True),  # 200, 300, 500, 1000
        sa.Column("qr_color", sa.String(7), nullable=True),  # hex color
        sa.Column("qr_logo_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "qr_error_correction",
            sa.String(1),
            nullable=False,
            server_default="M",
        ),  # L, M, Q, H
        # Audit fields
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Indexes for share_links
    op.create_index("ix_share_links_link_id", "share_links", ["link_id"], unique=True)
    op.create_index("ix_share_links_gallery_id", "share_links", ["gallery_id"])
    op.create_index("ix_share_links_status", "share_links", ["status"])

    # ===========================================
    # Table 4: gallery_assets
    # ===========================================
    op.create_table(
        "gallery_assets",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        # Parent gallery and sub-gallery
        sa.Column(
            "gallery_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("galleries.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "sub_gallery_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("sub_galleries.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        # Asset reference (from main assets table)
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("assets.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Gallery-specific metadata
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("pin_hash", sa.String(255), nullable=True),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(50)), nullable=True),
        # Denormalized interaction counts (updated via triggers)
        sa.Column("favorites_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("selections_count", sa.Integer(), nullable=False, server_default="0"),
        # Audit fields
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        # Unique constraint: asset can only appear once per gallery
        sa.UniqueConstraint("gallery_id", "asset_id", name="uq_gallery_asset"),
    )

    # Indexes for gallery_assets
    op.create_index("ix_gallery_assets_gallery_id", "gallery_assets", ["gallery_id"])
    op.create_index("ix_gallery_assets_sub_gallery_id", "gallery_assets", ["sub_gallery_id"])
    op.create_index("ix_gallery_assets_asset_id", "gallery_assets", ["asset_id"])
    op.create_index(
        "ix_gallery_assets_gallery_sort",
        "gallery_assets",
        ["gallery_id", "sort_order"],
    )
    # GIN index for tags array
    op.execute("CREATE INDEX ix_gallery_assets_tags ON gallery_assets USING gin (tags)")

    # ===========================================
    # Table 5: visitors
    # ===========================================
    op.create_table(
        "visitors",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        # Multi-tenancy
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Contact info
        sa.Column("email", sa.String(255), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        # Flexible metadata (JSONB)
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        # Audit fields
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        # Unique constraint: email unique per workspace
        sa.UniqueConstraint("workspace_id", "email", name="uq_visitor_workspace_email"),
    )

    # Indexes for visitors
    op.create_index("ix_visitors_workspace_id", "visitors", ["workspace_id"])
    op.create_index("ix_visitors_email", "visitors", ["email"])

    # ===========================================
    # Table 6: gallery_visitors (Access Log)
    # ===========================================
    op.create_table(
        "gallery_visitors",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        # References
        sa.Column(
            "visitor_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("visitors.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "gallery_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("galleries.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "link_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("share_links.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        # Access metadata
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("ip_address", sa.String(45), nullable=True),  # IPv6 support
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("referrer", sa.Text(), nullable=True),
    )

    # Indexes for gallery_visitors
    op.create_index("ix_gallery_visitors_visitor_id", "gallery_visitors", ["visitor_id"])
    op.create_index("ix_gallery_visitors_gallery_id", "gallery_visitors", ["gallery_id"])
    op.create_index("ix_gallery_visitors_link_id", "gallery_visitors", ["link_id"])
    op.create_index("ix_gallery_visitors_accessed_at", "gallery_visitors", ["accessed_at"])

    # ===========================================
    # Table 7: security_audit_log
    # ===========================================
    op.create_table(
        "security_audit_log",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        # References
        sa.Column(
            "gallery_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("galleries.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "link_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("share_links.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
            index=True,
        ),
        # Event details
        sa.Column(
            "event_type",
            sa.String(50),
            nullable=False,
            index=True,
        ),  # password_attempt, pin_attempt, rate_limit_violation
        sa.Column(
            "result",
            sa.String(20),
            nullable=False,
        ),  # success, failure, blocked
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("event_metadata", postgresql.JSONB(), nullable=True),
        # Client info
        sa.Column("ip_address", sa.String(45), nullable=True, index=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        # Timestamp
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
    )

    # Indexes for security_audit_log
    op.create_index("ix_security_audit_log_gallery_id", "security_audit_log", ["gallery_id"])
    op.create_index("ix_security_audit_log_event_type", "security_audit_log", ["event_type"])
    op.create_index("ix_security_audit_log_ip_address", "security_audit_log", ["ip_address"])
    op.create_index("ix_security_audit_log_created_at", "security_audit_log", ["created_at"])
    # Composite index for workspace+time queries
    op.create_index(
        "ix_security_audit_log_gallery_created",
        "security_audit_log",
        ["gallery_id", "created_at"],
    )

    # ===========================================
    # Circular Foreign Keys
    # ===========================================
    # Add FK for galleries.cover_asset_id → gallery_assets.id
    op.create_foreign_key(
        "fk_galleries_cover_asset",
        "galleries",
        "gallery_assets",
        ["cover_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add FK for sub_galleries.cover_asset_id → gallery_assets.id
    op.create_foreign_key(
        "fk_sub_galleries_cover_asset",
        "sub_galleries",
        "gallery_assets",
        ["cover_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Drop all gallery-service tables."""
    # Drop in reverse order to handle foreign keys
    op.drop_table("security_audit_log")
    op.drop_table("gallery_visitors")
    op.drop_table("visitors")
    op.drop_table("gallery_assets")
    op.drop_table("share_links")
    op.drop_table("sub_galleries")
    op.drop_table("galleries")
