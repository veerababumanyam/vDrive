"""Create galleries and assets tables

Revision ID: 003_galleries_assets
Revises: 002_workspaces
Create Date: 2025-01-01 00:02:00.000000

Tables:
- galleries: Photo gallery containers
- assets: Individual photos/files
- asset_versions: Version history for assets
- magic_links: Secure gallery access links
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_galleries_assets"
down_revision: Union[str, None] = "002_workspaces"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Galleries table
    op.create_table(
        "galleries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_asset_id", postgresql.UUID(as_uuid=True), nullable=True),  # FK added after assets table
        # Gallery settings
        sa.Column("event_date", sa.Date(), nullable=True),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=True),  # wedding, portrait, corporate, etc.
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),  # FK added in clients migration
        # Display settings
        sa.Column("layout", sa.String(50), nullable=False, server_default="grid"),  # grid, masonry, slideshow
        sa.Column("sort_order", sa.String(50), nullable=False, server_default="upload_date"),
        sa.Column("show_captions", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("show_download", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("allow_favorites", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allow_comments", sa.Boolean(), nullable=False, server_default="false"),
        # Selection settings
        sa.Column("selection_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("selection_limit", sa.Integer(), nullable=True),
        sa.Column("selection_deadline", sa.DateTime(timezone=True), nullable=True),
        # Watermark
        sa.Column("watermark_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("watermark_url", sa.String(2048), nullable=True),
        sa.Column("watermark_position", sa.String(20), nullable=True),
        sa.Column("watermark_opacity", sa.Float(), nullable=True),
        # Access control
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("require_email", sa.Boolean(), nullable=False, server_default="false"),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),  # draft, published, archived
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        # Counts (denormalized for performance)
        sa.Column("asset_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("workspace_id", "slug", name="uq_gallery_workspace_slug"),
    )

    # Indexes for galleries
    op.create_index("ix_galleries_workspace_id", "galleries", ["workspace_id"])
    op.create_index("ix_galleries_status", "galleries", ["status"])
    op.create_index("ix_galleries_event_date", "galleries", ["event_date"])
    op.create_index("ix_galleries_created_at", "galleries", ["created_at"])

    # Assets table
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gallery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("galleries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # File info
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=True),  # SHA-256
        # Storage
        sa.Column("storage_provider", sa.String(50), nullable=False, server_default="r2"),  # r2, s3, byos
        sa.Column("storage_key", sa.String(500), nullable=False),  # Full path in storage
        sa.Column("storage_bucket", sa.String(100), nullable=True),
        sa.Column("cdn_url", sa.String(2048), nullable=True),
        # Image dimensions
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("orientation", sa.Integer(), nullable=True),  # EXIF orientation
        sa.Column("aspect_ratio", sa.Float(), nullable=True),
        # Thumbnails
        sa.Column("thumbnail_url", sa.String(2048), nullable=True),
        sa.Column("thumbnail_key", sa.String(500), nullable=True),
        sa.Column("preview_url", sa.String(2048), nullable=True),
        sa.Column("preview_key", sa.String(500), nullable=True),
        # EXIF metadata
        sa.Column("exif_data", postgresql.JSONB(), nullable=True),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("camera_make", sa.String(100), nullable=True),
        sa.Column("camera_model", sa.String(100), nullable=True),
        sa.Column("lens", sa.String(100), nullable=True),
        sa.Column("focal_length", sa.String(20), nullable=True),
        sa.Column("aperture", sa.String(20), nullable=True),
        sa.Column("shutter_speed", sa.String(20), nullable=True),
        sa.Column("iso", sa.Integer(), nullable=True),
        sa.Column("gps_latitude", sa.Float(), nullable=True),
        sa.Column("gps_longitude", sa.Float(), nullable=True),
        # User-provided metadata
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("rating", sa.Integer(), nullable=True),  # 1-5
        sa.Column("color_label", sa.String(20), nullable=True),  # red, yellow, green, blue, purple
        # AI-generated metadata
        sa.Column("ai_tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("ai_description", sa.Text(), nullable=True),
        sa.Column("ai_analyzed_at", sa.DateTime(timezone=True), nullable=True),
        # Gallery position
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default="false"),
        # Selection
        sa.Column("is_selected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("selected_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("selected_at", sa.DateTime(timezone=True), nullable=True),
        # Processing status
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="pending"),  # pending, processing, completed, failed
        sa.Column("processing_error", sa.Text(), nullable=True),
        # Encryption
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("encryption_key_id", sa.String(100), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for assets
    op.create_index("ix_assets_workspace_id", "assets", ["workspace_id"])
    op.create_index("ix_assets_gallery_id", "assets", ["gallery_id"])
    op.create_index("ix_assets_taken_at", "assets", ["taken_at"])
    op.create_index("ix_assets_processing_status", "assets", ["processing_status"])
    op.create_index("ix_assets_file_hash", "assets", ["file_hash"])
    op.create_index("ix_assets_tags", "assets", ["tags"], postgresql_using="gin")
    op.create_index("ix_assets_ai_tags", "assets", ["ai_tags"], postgresql_using="gin")

    # Add foreign key for cover_asset_id in galleries
    op.create_foreign_key(
        "fk_galleries_cover_asset",
        "galleries", "assets",
        ["cover_asset_id"], ["id"],
        ondelete="SET NULL"
    )

    # Asset versions table
    op.create_table(
        "asset_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("change_note", sa.String(500), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("asset_id", "version_number", name="uq_asset_version"),
    )

    # Indexes for asset_versions
    op.create_index("ix_asset_versions_asset_id", "asset_versions", ["asset_id"])

    # Magic links table
    op.create_table(
        "magic_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("gallery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("galleries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=True),  # Optional name for the link
        sa.Column("email", sa.String(255), nullable=True),  # Associated email if known
        sa.Column("access_level", sa.String(20), nullable=False, server_default="view"),  # view, select, download
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Indexes for magic_links
    op.create_index("ix_magic_links_gallery_id", "magic_links", ["gallery_id"])
    op.create_index("ix_magic_links_token", "magic_links", ["token"])
    op.create_index("ix_magic_links_email", "magic_links", ["email"])


def downgrade() -> None:
    op.drop_table("magic_links")
    op.drop_table("asset_versions")
    op.drop_constraint("fk_galleries_cover_asset", "galleries", type_="foreignkey")
    op.drop_table("assets")
    op.drop_table("galleries")
