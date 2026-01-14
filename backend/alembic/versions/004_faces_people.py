"""Create faces and people tables

Revision ID: 004_faces_people
Revises: 003_galleries_assets
Create Date: 2025-01-01 00:03:00.000000

Tables:
- people: Named individuals for face recognition
- face_detections: Detected faces in assets
- face_embeddings: Vector embeddings for face recognition (pgvector)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_faces_people"
down_revision: Union[str, None] = "003_galleries_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # People table
    op.create_table(
        "people",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("relationship", sa.String(100), nullable=True),  # client, family, friend, etc.
        sa.Column("notes", sa.Text(), nullable=True),
        # Representative photo
        sa.Column("cover_face_id", postgresql.UUID(as_uuid=True), nullable=True),  # FK added after face_detections
        # Stats
        sa.Column("photo_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confirmed_count", sa.Integer(), nullable=False, server_default="0"),
        # Merge tracking
        sa.Column("merged_into_id", postgresql.UUID(as_uuid=True), nullable=True),  # Self-referential, for merged persons
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Self-referential FK for merged persons
    op.create_foreign_key(
        "fk_people_merged_into",
        "people", "people",
        ["merged_into_id"], ["id"],
        ondelete="SET NULL"
    )

    # Indexes for people
    op.create_index("ix_people_workspace_id", "people", ["workspace_id"])
    op.create_index("ix_people_name", "people", ["name"])
    op.create_index("ix_people_email", "people", ["email"])

    # Face detections table
    op.create_table(
        "face_detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people.id", ondelete="SET NULL"), nullable=True),
        # Bounding box (normalized 0-1)
        sa.Column("bbox_x", sa.Float(), nullable=False),
        sa.Column("bbox_y", sa.Float(), nullable=False),
        sa.Column("bbox_width", sa.Float(), nullable=False),
        sa.Column("bbox_height", sa.Float(), nullable=False),
        # Detection confidence
        sa.Column("detection_confidence", sa.Float(), nullable=False),
        sa.Column("recognition_confidence", sa.Float(), nullable=True),  # Confidence of person match
        # Face attributes (from AI)
        sa.Column("age_estimate", sa.Integer(), nullable=True),
        sa.Column("gender_estimate", sa.String(20), nullable=True),
        sa.Column("expression", sa.String(50), nullable=True),  # happy, neutral, sad, etc.
        sa.Column("facing_angle", sa.Float(), nullable=True),  # Degrees from frontal
        sa.Column("quality_score", sa.Float(), nullable=True),  # Face quality for recognition
        # Status
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default="false"),  # User confirmed this is correct
        sa.Column("is_rejected", sa.Boolean(), nullable=False, server_default="false"),  # User rejected this match
        sa.Column("confirmed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        # Thumbnail
        sa.Column("thumbnail_url", sa.String(2048), nullable=True),
        sa.Column("thumbnail_key", sa.String(500), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for face_detections
    op.create_index("ix_face_detections_workspace_id", "face_detections", ["workspace_id"])
    op.create_index("ix_face_detections_asset_id", "face_detections", ["asset_id"])
    op.create_index("ix_face_detections_person_id", "face_detections", ["person_id"])
    op.create_index("ix_face_detections_is_confirmed", "face_detections", ["is_confirmed"])

    # Add FK for cover_face_id in people
    op.create_foreign_key(
        "fk_people_cover_face",
        "people", "face_detections",
        ["cover_face_id"], ["id"],
        ondelete="SET NULL"
    )

    # Face embeddings table (pgvector)
    # Using 512-dimensional ArcFace embeddings
    # First ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create face_embeddings table with vector column using raw SQL
    op.execute("""
        CREATE TABLE face_embeddings (
            id UUID PRIMARY KEY,
            face_detection_id UUID NOT NULL UNIQUE REFERENCES face_detections(id) ON DELETE CASCADE,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            embedding vector(512) NOT NULL,
            model_name VARCHAR(100) NOT NULL DEFAULT 'arcface',
            model_version VARCHAR(50) NOT NULL DEFAULT '1.0',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # Create IVFFlat index for approximate nearest neighbor search
    # Lists = sqrt(rows), so starting with 100 lists for ~10k faces
    op.execute("""
        CREATE INDEX ix_face_embeddings_vector
        ON face_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    # Indexes for face_embeddings
    op.create_index("ix_face_embeddings_workspace_id", "face_embeddings", ["workspace_id"])
    op.create_index("ix_face_embeddings_face_detection_id", "face_embeddings", ["face_detection_id"])


def downgrade() -> None:
    op.drop_table("face_embeddings")
    op.drop_constraint("fk_people_cover_face", "people", type_="foreignkey")
    op.drop_table("face_detections")
    op.drop_constraint("fk_people_merged_into", "people", type_="foreignkey")
    op.drop_table("people")
    # Note: Don't drop pgvector extension as other tables might use it
