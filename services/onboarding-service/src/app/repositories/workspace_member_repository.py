"""
WorkspaceMember repository for database operations.

Handles all workspace membership database queries.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.workspace_member import WorkspaceMember, WorkspaceRole


class WorkspaceMemberRepository:
    """
    Data access layer for WorkspaceMember model.

    All methods operate on the async session passed in.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, member_id: str) -> Optional[WorkspaceMember]:
        """
        Get workspace member by ID.

        Args:
            member_id: UUID string of the membership

        Returns:
            WorkspaceMember if found, None otherwise
        """
        result = await self.db.execute(
            select(WorkspaceMember).where(WorkspaceMember.id == member_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_workspace(
        self,
        user_id: str,
        workspace_id: str,
    ) -> Optional[WorkspaceMember]:
        """
        Get membership for a specific user and workspace.

        Args:
            user_id: UUID of the user
            workspace_id: UUID of the workspace

        Returns:
            WorkspaceMember if found, None otherwise
        """
        result = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.workspace_id == workspace_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_workspaces(self, user_id: str) -> List[WorkspaceMember]:
        """
        Get all workspace memberships for a user.

        Args:
            user_id: UUID of the user

        Returns:
            List of WorkspaceMember instances
        """
        result = await self.db.execute(
            select(WorkspaceMember).where(WorkspaceMember.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_workspace_members(self, workspace_id: str) -> List[WorkspaceMember]:
        """
        Get all members of a workspace.

        Args:
            workspace_id: UUID of the workspace

        Returns:
            List of WorkspaceMember instances
        """
        result = await self.db.execute(
            select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
        )
        return list(result.scalars().all())

    async def create(
        self,
        user_id: str,
        workspace_id: str,
        role: WorkspaceRole = WorkspaceRole.OWNER,
        invited_by: Optional[str] = None,
    ) -> WorkspaceMember:
        """
        Create a new workspace membership.

        Args:
            user_id: UUID of the user
            workspace_id: UUID of the workspace
            role: Member role (default OWNER for workspace creators)
            invited_by: UUID of user who invited this member (optional)

        Returns:
            Created WorkspaceMember instance
        """
        member = WorkspaceMember(
            user_id=user_id,
            workspace_id=workspace_id,
            role=role,
            invited_by=invited_by,
        )

        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def is_member(self, user_id: str, workspace_id: str) -> bool:
        """
        Check if user is a member of workspace.

        Args:
            user_id: UUID of the user
            workspace_id: UUID of the workspace

        Returns:
            True if user is a member, False otherwise
        """
        result = await self.db.execute(
            select(WorkspaceMember.id).where(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.workspace_id == workspace_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_owner(self, user_id: str, workspace_id: str) -> bool:
        """
        Check if user is the owner of workspace.

        Args:
            user_id: UUID of the user
            workspace_id: UUID of the workspace

        Returns:
            True if user is owner, False otherwise
        """
        result = await self.db.execute(
            select(WorkspaceMember.id).where(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == WorkspaceRole.OWNER,
            )
        )
        return result.scalar_one_or_none() is not None
