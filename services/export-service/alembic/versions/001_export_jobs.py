"""Create export_jobs table

Revision ID: 001_export_jobs
Revises:
Create Date: 2026-01-16 10:00:00.000000

Tables:
- export_jobs: Asynchronous export job tracking with progress and status
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_export_jobs"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Export jobs table
    op.create_table(
        "export_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        # Export configuration
        sa.Column("export_type", sa.String(50), nullable=False),  # workspace, gallery, selection
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),  # pending, processing, completed, failed, cancelled
        sa.Column("options", postgresql.JSONB(), nullable=True),  # Flexible export options
        # Progress tracking
        sa.Column("total_assets", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_assets", sa.Integer(), nullable=False, server_default="0"),
        # Result
        sa.Column("file_url", sa.String(2048), nullable=True),  # Presigned R2 URL
        sa.Column("file_size", sa.Integer(), nullable=True),  # Size in bytes
        sa.Column("file_key", sa.String(500), nullable=True),  # R2 storage key
        # Error handling
        sa.Column("error_message", sa.Text(), nullable=True),
        # Expiration
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Indexes for export_jobs
    op.create_index("ix_export_jobs_workspace_id", "export_jobs", ["workspace_id"])
    op.create_index("ix_export_jobs_user_id", "export_jobs", ["user_id"])
    op.create_index("ix_export_jobs_status", "export_jobs", ["status"])
    op.create_index("ix_export_jobs_export_type", "export_jobs", ["export_type"])
    op.create_index("ix_export_jobs_created_at", "export_jobs", ["created_at"])

    # Composite index for common query pattern (workspace + status)
    op.create_index(
        "ix_export_jobs_workspace_status",
        "export_jobs",
        ["workspace_id", "status"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_export_jobs_workspace_status", table_name="export_jobs")
    op.drop_index("ix_export_jobs_created_at", table_name="export_jobs")
    op.drop_index("ix_export_jobs_export_type", table_name="export_jobs")
    op.drop_index("ix_export_jobs_status", table_name="export_jobs")
    op.drop_index("ix_export_jobs_user_id", table_name="export_jobs")
    op.drop_index("ix_export_jobs_workspace_id", table_name="export_jobs")

    # Drop table
    op.drop_table("export_jobs")
