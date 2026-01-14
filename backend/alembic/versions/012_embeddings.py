"""Create photo embeddings table for semantic search

Revision ID: 012_embeddings
Revises: 011_audit
Create Date: 2025-01-01 00:11:00.000000

Tables:
- photo_embeddings: CLIP embeddings for semantic photo search (pgvector)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "012_embeddings"
down_revision: Union[str, None] = "011_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgvector extension exists (already created in 004_faces_people)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Photo embeddings table
    # Using 1536-dimensional CLIP embeddings for semantic search
    op.create_table(
        "photo_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        # Embedding vector (1536 dimensions for OpenAI CLIP / text-embedding-3-large)
        # Note: Use raw SQL for vector type
        sa.Column("embedding", sa.LargeBinary(), nullable=False),  # Placeholder, replaced with vector
        # Model information
        sa.Column("model_name", sa.String(100), nullable=False, server_default="clip"),
        sa.Column("model_version", sa.String(50), nullable=False, server_default="ViT-L/14"),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False, server_default="1536"),
        # Content analysis results (cached for quick access)
        sa.Column("detected_objects", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("detected_scenes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("detected_activities", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("color_palette", postgresql.ARRAY(sa.String()), nullable=True),  # Dominant colors
        sa.Column("aesthetic_score", sa.Float(), nullable=True),  # 0-1 aesthetic quality
        sa.Column("technical_score", sa.Float(), nullable=True),  # 0-1 technical quality
        # Text description (for RAG)
        sa.Column("generated_caption", sa.Text(), nullable=True),
        sa.Column("generated_tags", postgresql.ARRAY(sa.String()), nullable=True),
        # Processing status
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="pending"),
        # pending, processing, completed, failed
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Alter column to vector type
    op.execute("""
        ALTER TABLE photo_embeddings
        ALTER COLUMN embedding TYPE vector(1536)
        USING embedding::vector(1536)
    """)

    # Create HNSW index for approximate nearest neighbor search
    # HNSW is generally better than IVFFlat for smaller datasets and provides better recall
    op.execute("""
        CREATE INDEX ix_photo_embeddings_vector_hnsw
        ON photo_embeddings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Standard indexes
    op.create_index("ix_photo_embeddings_workspace_id", "photo_embeddings", ["workspace_id"])
    op.create_index("ix_photo_embeddings_asset_id", "photo_embeddings", ["asset_id"])
    op.create_index("ix_photo_embeddings_processing_status", "photo_embeddings", ["processing_status"])
    op.create_index("ix_photo_embeddings_model_name", "photo_embeddings", ["model_name"])

    # GIN indexes for array columns
    op.create_index("ix_photo_embeddings_detected_objects", "photo_embeddings", ["detected_objects"], postgresql_using="gin")
    op.create_index("ix_photo_embeddings_detected_scenes", "photo_embeddings", ["detected_scenes"], postgresql_using="gin")
    op.create_index("ix_photo_embeddings_generated_tags", "photo_embeddings", ["generated_tags"], postgresql_using="gin")

    # Add helper function for semantic search
    op.execute("""
        CREATE OR REPLACE FUNCTION semantic_search(
            query_embedding vector(1536),
            workspace_uuid uuid,
            match_threshold float DEFAULT 0.5,
            match_count int DEFAULT 20
        )
        RETURNS TABLE (
            asset_id uuid,
            similarity float
        )
        LANGUAGE sql STABLE
        AS $$
            SELECT
                pe.asset_id,
                1 - (pe.embedding <=> query_embedding) as similarity
            FROM photo_embeddings pe
            WHERE pe.workspace_id = workspace_uuid
                AND pe.processing_status = 'completed'
                AND 1 - (pe.embedding <=> query_embedding) > match_threshold
            ORDER BY pe.embedding <=> query_embedding
            LIMIT match_count;
        $$;
    """)

    # Add helper function for finding similar photos
    op.execute("""
        CREATE OR REPLACE FUNCTION find_similar_photos(
            source_asset_uuid uuid,
            workspace_uuid uuid,
            match_count int DEFAULT 10
        )
        RETURNS TABLE (
            asset_id uuid,
            similarity float
        )
        LANGUAGE sql STABLE
        AS $$
            SELECT
                pe.asset_id,
                1 - (pe.embedding <=> source.embedding) as similarity
            FROM photo_embeddings pe
            CROSS JOIN (
                SELECT embedding
                FROM photo_embeddings
                WHERE asset_id = source_asset_uuid
            ) source
            WHERE pe.workspace_id = workspace_uuid
                AND pe.asset_id != source_asset_uuid
                AND pe.processing_status = 'completed'
            ORDER BY pe.embedding <=> source.embedding
            LIMIT match_count;
        $$;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS find_similar_photos(uuid, uuid, int)")
    op.execute("DROP FUNCTION IF EXISTS semantic_search(vector, uuid, float, int)")
    op.drop_table("photo_embeddings")
