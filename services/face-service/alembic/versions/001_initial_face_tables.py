"""Initial face tables with pgvector.

Revision ID: 001
Revises:
Create Date: 2026-01-15

Creates:
- faces: Detected faces with bounding boxes
- face_groups: Groups of faces (people)
- face_embeddings: 512-dim vectors with IVFFlat index
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create face_groups table first (referenced by faces)
    op.create_table(
        "face_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("representative_face_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("face_count", sa.String(10), server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    # Create faces table
    op.create_table(
        "faces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bounding_box", postgresql.JSONB, nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("landmarks", postgresql.JSONB, nullable=True),
        sa.Column("embedding_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("face_groups.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("detection_metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    # Create face_embeddings table with pgvector
    op.create_table(
        "face_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "face_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("faces.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("embedding", sa.Column.__class__, nullable=False),  # vector(512)
        sa.Column("model_name", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    # Manually create vector column since SQLAlchemy migration doesn't handle it well
    op.execute(
        "ALTER TABLE face_embeddings ADD COLUMN IF NOT EXISTS embedding vector(512) NOT NULL"
    )

    # Add foreign key from face_groups to faces for representative_face
    op.create_foreign_key(
        "fk_face_groups_representative_face",
        "face_groups",
        "faces",
        ["representative_face_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add foreign key from faces to face_embeddings
    op.create_foreign_key(
        "fk_faces_embedding",
        "faces",
        "face_embeddings",
        ["embedding_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create indexes
    op.create_index("ix_faces_asset_id", "faces", ["asset_id"])
    op.create_index("ix_faces_workspace_id", "faces", ["workspace_id"])
    op.create_index("ix_faces_group_id", "faces", ["group_id"])
    op.create_index("ix_faces_workspace_asset", "faces", ["workspace_id", "asset_id"])
    op.create_index("ix_faces_workspace_group", "faces", ["workspace_id", "group_id"])

    op.create_index("ix_face_groups_workspace_id", "face_groups", ["workspace_id"])
    op.create_index("ix_face_groups_workspace_name", "face_groups", ["workspace_id", "name"])

    # Create IVFFlat index for face embeddings (approximate nearest neighbor)
    # lists = 100 is good for up to 100k vectors
    op.execute(
        """
        CREATE INDEX ix_face_embeddings_vector
        ON face_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_face_embeddings_vector", table_name="face_embeddings")
    op.drop_index("ix_face_groups_workspace_name", table_name="face_groups")
    op.drop_index("ix_face_groups_workspace_id", table_name="face_groups")
    op.drop_index("ix_faces_workspace_group", table_name="faces")
    op.drop_index("ix_faces_workspace_asset", table_name="faces")
    op.drop_index("ix_faces_group_id", table_name="faces")
    op.drop_index("ix_faces_workspace_id", table_name="faces")
    op.drop_index("ix_faces_asset_id", table_name="faces")

    # Drop foreign keys
    op.drop_constraint("fk_faces_embedding", "faces", type_="foreignkey")
    op.drop_constraint("fk_face_groups_representative_face", "face_groups", type_="foreignkey")

    # Drop tables in reverse order
    op.drop_table("face_embeddings")
    op.drop_table("faces")
    op.drop_table("face_groups")
