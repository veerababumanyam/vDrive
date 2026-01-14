"""create_assets

Revision ID: 002
Revises: 001
Create Date: 2026-01-14 00:10:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create assets table for processed files."""
    op.create_table(
        'assets',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('upload_id', postgresql.UUID(as_uuid=False), sa.ForeignKey('uploads.id', ondelete='SET NULL'), unique=True),
        sa.Column('original_key', sa.String(500), nullable=False),
        sa.Column('thumbnail_key', sa.String(500)),
        sa.Column('preview_key', sa.String(500)),
        sa.Column('lqip_base64', sa.Text()),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('width', sa.Integer()),
        sa.Column('height', sa.Integer()),
        sa.Column('duration_seconds', sa.Numeric(10, 2)),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('encryption_key_id', sa.String(100), index=True),
        sa.Column('encryption_iv', sa.LargeBinary()),
        sa.Column('encryption_tag', sa.LargeBinary()),
        sa.Column('processing_status', sa.String(20), nullable=False, index=True, server_default='pending'),
        sa.Column('processing_error', sa.Text()),
        sa.Column('checksum', sa.String(64), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_index('idx_asset_workspace_created', 'assets', ['workspace_id', sa.text('created_at DESC')])
    op.create_index('idx_asset_processing', 'assets', ['processing_status'],
                    postgresql_where=sa.text("processing_status != 'completed'"))


def downgrade() -> None:
    """Drop assets table."""
    op.drop_table('assets')
