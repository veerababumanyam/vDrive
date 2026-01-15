"""Initial photo embedding tables with HNSW index.

Revision ID: 001
Revises: None
Create Date: 2024-01-15
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create photo_embeddings table with HNSW vector index."""

    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create photo_embeddings table
    op.create_table(
        "photo_embeddings",
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
            "embedding",
            Vector(1536),
            nullable=False,
        ),
        sa.Column(
            "model_name",
            sa.String(100),
            nullable=False,
            server_default="clip-ViT-L-14",
        ),
        sa.Column(
            "model_version",
            sa.String(50),
            nullable=False,
            server_default="1.0",
        ),
        sa.Column(
            "image_description",
            sa.Text,
            nullable=True,
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

    # Create standard indexes
    op.create_index(
        "idx_photo_embeddings_workspace",
        "photo_embeddings",
        ["workspace_id"],
    )
    op.create_index(
        "idx_photo_embeddings_asset",
        "photo_embeddings",
        ["asset_id"],
    )

    # Create HNSW index for fast semantic similarity search
    # HNSW (Hierarchical Navigable Small World) provides:
    # - Faster queries than IVFFlat at the cost of more memory
    # - Good recall (typically >95%) with appropriate parameters
    # - m=16: Number of connections per layer
    # - ef_construction=64: Size of dynamic candidate list during construction
    op.execute(
        """
        CREATE INDEX idx_photo_embeddings_hnsw
        ON photo_embeddings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    """Drop photo_embeddings table and indexes."""

    op.drop_index("idx_photo_embeddings_hnsw", table_name="photo_embeddings")
    op.drop_index("idx_photo_embeddings_asset", table_name="photo_embeddings")
    op.drop_index("idx_photo_embeddings_workspace", table_name="photo_embeddings")
    op.drop_table("photo_embeddings")
