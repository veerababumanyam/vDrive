"""Create workspaces and multi-tenancy tables

Revision ID: 002_workspaces
Revises: 001_users_auth
Create Date: 2025-01-01 00:01:00.000000

Tables:
- workspaces: Multi-tenant workspace containers
- workspace_members: User-workspace relationships
- workspace_invites: Pending workspace invitations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_workspaces"
down_revision: Union[str, None] = "001_users_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Workspaces table
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(2048), nullable=True),
        sa.Column("cover_url", sa.String(2048), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("date_format", sa.String(20), nullable=False, server_default="YYYY-MM-DD"),
        # Branding
        sa.Column("primary_color", sa.String(7), nullable=True),  # Hex color
        sa.Column("secondary_color", sa.String(7), nullable=True),
        sa.Column("custom_domain", sa.String(255), nullable=True),
        sa.Column("custom_domain_verified", sa.Boolean(), nullable=False, server_default="false"),
        # Settings
        sa.Column("settings", postgresql.JSONB(), nullable=False, server_default="{}"),
        # Limits (based on subscription)
        sa.Column("storage_limit_bytes", sa.BigInteger(), nullable=False, server_default="10737418240"),  # 10GB
        sa.Column("storage_used_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("member_limit", sa.Integer(), nullable=False, server_default="5"),
        # Status
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suspended_reason", sa.String(500), nullable=True),
        # Owner
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes for workspaces
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"])
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"])
    op.create_index("ix_workspaces_custom_domain", "workspaces", ["custom_domain"], unique=True, postgresql_where=sa.text("custom_domain IS NOT NULL"))

    # Workspace members table
    op.create_table(
        "workspace_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),  # owner, admin, member, viewer
        sa.Column("permissions", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("title", sa.String(100), nullable=True),  # Job title
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("invited_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
    )

    # Indexes for workspace_members
    op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"])
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])
    op.create_index("ix_workspace_members_role", "workspace_members", ["role"])

    # Workspace invites table
    op.create_table(
        "workspace_invites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("invited_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),  # pending, accepted, expired, revoked
        sa.Column("accepted_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Indexes for workspace_invites
    op.create_index("ix_workspace_invites_workspace_id", "workspace_invites", ["workspace_id"])
    op.create_index("ix_workspace_invites_email", "workspace_invites", ["email"])
    op.create_index("ix_workspace_invites_token", "workspace_invites", ["token"])
    op.create_index("ix_workspace_invites_status", "workspace_invites", ["status"])

    # Add default workspace to users table
    op.add_column("users", sa.Column("default_workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "default_workspace_id")
    op.drop_table("workspace_invites")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
