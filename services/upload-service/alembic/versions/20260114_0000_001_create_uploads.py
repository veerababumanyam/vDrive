"""create_uploads

Revision ID: 001
Revises:
Create Date: 2026-01-14 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create uploads table for TUS resumable upload tracking."""
    op.create_table(
        'uploads',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('expected_size', sa.BigInteger(), nullable=False),
        sa.Column('received_bytes', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, index=True, server_default='created'),
        sa.Column('upload_url', sa.String(500), unique=True),
        sa.Column('storage_path', sa.String(500)),
        sa.Column('checksum_client', sa.String(64)),
        sa.Column('checksum_server', sa.String(64)),
        sa.Column('multipart_upload_id', sa.String(100)),
        sa.Column('parts_metadata', postgresql.JSONB, server_default='[]'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('expected_size > 0', name='check_expected_size_positive'),
        sa.CheckConstraint('received_bytes >= 0', name='check_received_bytes_non_negative'),
        sa.CheckConstraint('received_bytes <= expected_size', name='check_received_bytes_within_expected'),
        sa.CheckConstraint("expected_size <= 10737418240", name='check_max_file_size_10gb'),
    )

    # Composite indexes
    op.create_index('idx_upload_workspace_status', 'uploads', ['workspace_id', 'status'])
    op.create_index('idx_upload_expires', 'uploads', ['expires_at'],
                    postgresql_where=sa.text("status IN ('created', 'uploading')"))
    op.create_index('idx_upload_user', 'uploads', ['user_id', sa.text('created_at DESC')])


def downgrade() -> None:
    """Drop uploads table."""
    op.drop_table('uploads')
