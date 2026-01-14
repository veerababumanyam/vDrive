"""Create albums tables

Revision ID: 009_albums
Revises: 008_webhooks
Create Date: 2025-01-01 00:08:00.000000

Tables:
- albums: Photo album/book designs
- album_spreads: Individual spreads/pages in albums
- album_photos: Photos placed in album spreads
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "009_albums"
down_revision: Union[str, None] = "008_webhooks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Albums table
    op.create_table(
        "albums",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gallery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("galleries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="SET NULL"), nullable=True),
        # Album details
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("album_type", sa.String(50), nullable=False, server_default="photo_book"),
        # photo_book, layflat, magazine, flush_mount
        # Physical specifications
        sa.Column("size", sa.String(50), nullable=False, server_default="10x10"),  # e.g., 8x8, 10x10, 12x12
        sa.Column("orientation", sa.String(20), nullable=False, server_default="square"),  # square, landscape, portrait
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("cover_type", sa.String(50), nullable=True),  # hardcover, softcover, leather, fabric
        sa.Column("paper_type", sa.String(50), nullable=True),  # matte, glossy, silk, luster
        # Cover image
        sa.Column("cover_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cover_layout", postgresql.JSONB(), nullable=True),  # Cover design settings
        # Template/theme
        sa.Column("template_id", sa.String(100), nullable=True),
        sa.Column("theme_settings", postgresql.JSONB(), nullable=False, server_default="{}"),
        # background colors, fonts, styles
        # Pricing
        sa.Column("base_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("extra_page_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("total_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        # Status
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        # draft, in_progress, review, approved, ordered, shipped, delivered
        sa.Column("client_can_edit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("client_approved_at", sa.DateTime(timezone=True), nullable=True),
        # Order info
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("order_reference", sa.String(100), nullable=True),
        sa.Column("shipping_address", postgresql.JSONB(), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tracking_number", sa.String(100), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        # Created by
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for albums
    op.create_index("ix_albums_workspace_id", "albums", ["workspace_id"])
    op.create_index("ix_albums_gallery_id", "albums", ["gallery_id"])
    op.create_index("ix_albums_client_id", "albums", ["client_id"])
    op.create_index("ix_albums_status", "albums", ["status"])

    # Album spreads table
    op.create_table(
        "album_spreads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("album_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("albums.id", ondelete="CASCADE"), nullable=False),
        # Spread position
        sa.Column("spread_number", sa.Integer(), nullable=False),  # 0 = cover, 1 = first spread, etc.
        sa.Column("is_cover", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_back_cover", sa.Boolean(), nullable=False, server_default="false"),
        # Layout
        sa.Column("layout_template_id", sa.String(100), nullable=True),  # Reference to layout template
        sa.Column("layout", postgresql.JSONB(), nullable=False, server_default="{}"),  # Custom layout data
        # Background
        sa.Column("background_color", sa.String(7), nullable=True),  # Hex color
        sa.Column("background_image_url", sa.String(2048), nullable=True),
        sa.Column("background_opacity", sa.Float(), nullable=True),
        # Text overlays
        sa.Column("text_elements", postgresql.JSONB(), nullable=False, server_default="[]"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("album_id", "spread_number", name="uq_album_spread_number"),
    )

    # Indexes for album_spreads
    op.create_index("ix_album_spreads_album_id", "album_spreads", ["album_id"])

    # Album photos table
    op.create_table(
        "album_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("album_spread_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("album_spreads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="SET NULL"), nullable=True),
        # Position on spread (normalized 0-1)
        sa.Column("position_x", sa.Float(), nullable=False),
        sa.Column("position_y", sa.Float(), nullable=False),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("rotation", sa.Float(), nullable=False, server_default="0"),  # Degrees
        sa.Column("z_index", sa.Integer(), nullable=False, server_default="0"),
        # Image adjustments
        sa.Column("crop", postgresql.JSONB(), nullable=True),  # {x, y, width, height} - crop area
        sa.Column("zoom", sa.Float(), nullable=False, server_default="1"),
        sa.Column("flip_horizontal", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("flip_vertical", sa.Boolean(), nullable=False, server_default="false"),
        # Styling
        sa.Column("border_width", sa.Float(), nullable=True),
        sa.Column("border_color", sa.String(7), nullable=True),
        sa.Column("shadow", postgresql.JSONB(), nullable=True),  # {offsetX, offsetY, blur, color}
        sa.Column("opacity", sa.Float(), nullable=False, server_default="1"),
        # Mask/frame
        sa.Column("mask_id", sa.String(100), nullable=True),  # Reference to mask template
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for album_photos
    op.create_index("ix_album_photos_album_spread_id", "album_photos", ["album_spread_id"])
    op.create_index("ix_album_photos_asset_id", "album_photos", ["asset_id"])


def downgrade() -> None:
    op.drop_table("album_photos")
    op.drop_table("album_spreads")
    op.drop_table("albums")
