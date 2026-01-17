"""Create migration_jobs table

Revision ID: 002_migration_jobs
Revises: 001_export_jobs
Create Date: 2026-01-16 11:00:00.000000

Tables:
- migration_jobs: Asynchronous migration job tracking for importing from competitor platforms
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_migration_jobs"
down_revision: Union[str, None] = "001_export_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migration jobs table
    op.create_table(
        "migration_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        # Migration configuration
        sa.Column("platform", sa.String(50), nullable=False),  # pixieset, pic-time, shootproof, zenfolio, smugmug
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),  # pending, processing, completed, failed, cancelled
        sa.Column("options", postgresql.JSONB(), nullable=True),  # Flexible migration options
        sa.Column("credentials", postgresql.JSONB(), nullable=True),  # Platform credentials (encrypted in production)
        # Progress tracking - Assets
        sa.Column("total_assets", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_assets", sa.Integer(), nullable=False, server_default="0"),
        # Progress tracking - Galleries
        sa.Column("total_galleries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_galleries", sa.Integer(), nullable=False, server_default="0"),
        # Error handling
        sa.Column("error_message", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for migration_jobs
    op.create_index("ix_migration_jobs_workspace_id", "migration_jobs", ["workspace_id"])
    op.create_index("ix_migration_jobs_user_id", "migration_jobs", ["user_id"])
    op.create_index("ix_migration_jobs_status", "migration_jobs", ["status"])
    op.create_index("ix_migration_jobs_platform", "migration_jobs", ["platform"])
    op.create_index("ix_migration_jobs_created_at", "migration_jobs", ["created_at"])

    # Composite index for common query pattern (workspace + status)
    op.create_index(
        "ix_migration_jobs_workspace_status",
        "migration_jobs",
        ["workspace_id", "status"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_migration_jobs_workspace_status", table_name="migration_jobs")
    op.drop_index("ix_migration_jobs_created_at", table_name="migration_jobs")
    op.drop_index("ix_migration_jobs_platform", table_name="migration_jobs")
    op.drop_index("ix_migration_jobs_status", table_name="migration_jobs")
    op.drop_index("ix_migration_jobs_user_id", table_name="migration_jobs")
    op.drop_index("ix_migration_jobs_workspace_id", table_name="migration_jobs")

    # Drop table
    op.drop_table("migration_jobs")
