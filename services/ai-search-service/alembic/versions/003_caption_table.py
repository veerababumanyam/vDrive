"""Add captions table for AI-generated photo captions.

Revision ID: 003
Revises: 002
Create Date: 2024-01-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create captions table for AI-generated suggestions."""

    # Create caption style enum
    caption_style = postgresql.ENUM(
        "professional",
        "casual",
        "seo",
        "social_media",
        name="captionstyle",
        create_type=False,
    )
    caption_style.create(op.get_bind(), checkfirst=True)

    # Create captions table
    op.create_table(
        "captions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "suggestions",
            postgresql.JSONB,
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "selected_caption",
            sa.String(1000),
            nullable=True,
        ),
        sa.Column(
            "preferred_style",
            sa.Enum(
                "professional",
                "casual",
                "seo",
                "social_media",
                name="captionstyle",
            ),
            nullable=False,
            server_default="professional",
        ),
        sa.Column(
            "detected_context",
            postgresql.JSONB,
            nullable=True,
        ),
        sa.Column(
            "model_name",
            sa.String(100),
            nullable=False,
            server_default="gemini-2.0-flash",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create indexes
    op.create_index(
        "idx_captions_asset",
        "captions",
        ["asset_id"],
    )
    op.create_index(
        "idx_captions_workspace",
        "captions",
        ["workspace_id"],
    )


def downgrade() -> None:
    """Drop captions table."""

    op.drop_index("idx_captions_workspace", table_name="captions")
    op.drop_index("idx_captions_asset", table_name="captions")
    op.drop_table("captions")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS captionstyle")
