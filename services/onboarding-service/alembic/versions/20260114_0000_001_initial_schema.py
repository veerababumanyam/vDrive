"""Initial schema with users, workspaces, verification tokens, and onboarding state

Revision ID: 001
Revises:
Create Date: 2026-01-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration changes."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("terms_accepted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("privacy_accepted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("privacy_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("theme_preference", sa.String(20), nullable=False, server_default="system"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)

    # Create workspaces table
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "business_type",
            sa.String(20),
            nullable=False,
            server_default="other",
        ),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("date_format", sa.String(20), nullable=False, server_default="YYYY-MM-DD"),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("brand_color", sa.String(7), nullable=True),
        sa.Column(
            "subscription_tier",
            sa.String(20),
            nullable=False,
            server_default="trial",
        ),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("storage_limit_gb", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("ai_credits", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("max_team_members", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"], unique=True)
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"])

    # Create workspace_members table
    op.create_table(
        "workspace_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM('owner', 'admin', 'editor', 'viewer', name='workspace_role', create_type=True),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column("permissions", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("invited_by", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "workspace_id", name="uq_workspace_member_user_workspace"),
    )
    op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"])
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])

    # Create verification_tokens table
    op.create_table(
        "verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("token_type", sa.String(20), nullable=False, server_default="email_verification"),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_verification_tokens_token_hash", "verification_tokens", ["token_hash"], unique=True)
    op.create_index("ix_verification_tokens_user_id", "verification_tokens", ["user_id"])

    # Create onboarding_states table
    # Note: enum type is created automatically by SQLAlchemy when first used
    op.create_table(
        "onboarding_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "current_step",
            postgresql.ENUM(
                'registration', 'email_verification', 'workspace_identity',
                'workspace_preferences', 'workspace_branding', 'completed',
                name='onboarding_step',
                create_type=True,
            ),
            nullable=False,
            server_default="registration",
        ),
        sa.Column("completed_steps", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("form_data", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("activation_checklist", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("checklist_dismissed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_onboarding_states_user_id", "onboarding_states", ["user_id"], unique=True)


def downgrade() -> None:
    """Revert migration changes."""
    op.drop_index("ix_onboarding_states_user_id", table_name="onboarding_states")
    op.drop_table("onboarding_states")

    # Drop the onboarding_step enum type
    onboarding_step_enum = postgresql.ENUM(name='onboarding_step')
    onboarding_step_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_verification_tokens_user_id", table_name="verification_tokens")
    op.drop_index("ix_verification_tokens_token_hash", table_name="verification_tokens")
    op.drop_table("verification_tokens")

    op.drop_index("ix_workspace_members_user_id", table_name="workspace_members")
    op.drop_index("ix_workspace_members_workspace_id", table_name="workspace_members")
    op.drop_table("workspace_members")

    # Drop the workspace_role enum type
    workspace_role_enum = postgresql.ENUM(name='workspace_role')
    workspace_role_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_workspaces_owner_id", table_name="workspaces")
    op.drop_index("ix_workspaces_slug", table_name="workspaces")
    op.drop_table("workspaces")

    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
