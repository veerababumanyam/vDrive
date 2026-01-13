"""
WorkspaceMember model for user-workspace associations.

Links users to workspaces with role-based permissions.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Dict, List
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base

if TYPE_CHECKING:
    from src.app.models.user import User
    from src.app.models.workspace import Workspace


class WorkspaceRole(str, Enum):
    """Workspace member roles with hierarchical permissions."""

    OWNER = "owner"      # Full access, can delete workspace
    ADMIN = "admin"      # Full access, cannot delete workspace
    EDITOR = "editor"    # Can create/edit galleries
    VIEWER = "viewer"    # Read-only access


# Default permissions by role
DEFAULT_PERMISSIONS: Dict[WorkspaceRole, List[str]] = {
    WorkspaceRole.OWNER: [
        "workspace:delete",
        "workspace:settings",
        "members:manage",
        "billing:manage",
        "galleries:create",
        "galleries:edit",
        "galleries:delete",
        "galleries:publish",
        "assets:upload",
        "assets:delete",
        "ai:use",
    ],
    WorkspaceRole.ADMIN: [
        "workspace:settings",
        "members:manage",
        "galleries:create",
        "galleries:edit",
        "galleries:delete",
        "galleries:publish",
        "assets:upload",
        "assets:delete",
        "ai:use",
    ],
    WorkspaceRole.EDITOR: [
        "galleries:create",
        "galleries:edit",
        "galleries:publish",
        "assets:upload",
        "ai:use",
    ],
    WorkspaceRole.VIEWER: [
        "galleries:view",
        "assets:view",
    ],
}


class WorkspaceMember(Base):
    """
    Workspace membership model.

    Associates users with workspaces and defines their role/permissions.
    """

    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("user_id", "workspace_id", name="uq_workspace_member_user_workspace"),
    )

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Foreign keys
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Role
    role: Mapped[WorkspaceRole] = mapped_column(
        SQLEnum(WorkspaceRole, name="workspace_role"),
        nullable=False,
        default=WorkspaceRole.VIEWER,
    )

    # Custom permissions (overrides role defaults if set)
    permissions: Mapped[Dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Invitation tracking
    invited_by: Mapped[str] = mapped_column(
        String(36),  # User ID who invited this member
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="workspace_memberships",
        lazy="selectin",
    )
    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="members",
        lazy="selectin",
    )

    @property
    def effective_permissions(self) -> List[str]:
        """
        Get effective permissions combining role defaults and custom permissions.

        Custom permissions override role defaults if set.
        """
        # Start with role default permissions
        base_permissions = set(DEFAULT_PERMISSIONS.get(self.role, []))

        # Apply custom permissions if set
        if self.permissions:
            granted = set(self.permissions.get("granted", []))
            revoked = set(self.permissions.get("revoked", []))
            base_permissions = (base_permissions | granted) - revoked

        return list(base_permissions)

    def has_permission(self, permission: str) -> bool:
        """Check if member has a specific permission."""
        return permission in self.effective_permissions

    @property
    def is_owner(self) -> bool:
        """Check if member is workspace owner."""
        return self.role == WorkspaceRole.OWNER

    @property
    def is_admin(self) -> bool:
        """Check if member is workspace admin or owner."""
        return self.role in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN)

    def __repr__(self) -> str:
        return f"<WorkspaceMember user={self.user_id} workspace={self.workspace_id} role={self.role.value}>"
