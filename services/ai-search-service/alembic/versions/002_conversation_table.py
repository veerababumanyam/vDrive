"""Add conversation table for RAG chat.

Revision ID: 002
Revises: 001
Create Date: 2024-01-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create conversations table for RAG chat history."""

    # Create conversation status enum
    conversation_status = postgresql.ENUM(
        "active",
        "archived",
        "deleted",
        name="conversationstatus",
        create_type=False,
    )
    conversation_status.create(op.get_bind(), checkfirst=True)

    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "title",
            sa.String(255),
            nullable=True,
        ),
        sa.Column(
            "messages",
            postgresql.JSONB,
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "referenced_photos",
            postgresql.JSONB,
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "archived",
                "deleted",
                name="conversationstatus",
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "summary",
            sa.Text,
            nullable=True,
        ),
        sa.Column(
            "message_count",
            sa.Integer,
            nullable=False,
            server_default="0",
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
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create indexes
    op.create_index(
        "idx_conversations_workspace",
        "conversations",
        ["workspace_id"],
    )
    op.create_index(
        "idx_conversations_user",
        "conversations",
        ["user_id"],
    )
    op.create_index(
        "idx_conversations_status",
        "conversations",
        ["status"],
    )
    op.create_index(
        "idx_conversations_last_activity",
        "conversations",
        ["last_activity_at"],
    )


def downgrade() -> None:
    """Drop conversations table."""

    op.drop_index("idx_conversations_last_activity", table_name="conversations")
    op.drop_index("idx_conversations_status", table_name="conversations")
    op.drop_index("idx_conversations_user", table_name="conversations")
    op.drop_index("idx_conversations_workspace", table_name="conversations")
    op.drop_table("conversations")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS conversationstatus")
