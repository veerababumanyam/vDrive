"""Workspace isolation and validation."""

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Upload, Asset
from .auth import CurrentUser

logger = structlog.get_logger()


async def validate_workspace_access(
    workspace_id: str,
    current_user: CurrentUser,
):
    """
    Validate that current user has access to workspace.

    Args:
        workspace_id: Workspace ID to check
        current_user: Authenticated user

    Raises:
        HTTPException: If user doesn't have access to workspace
    """
    if current_user.workspace_id != workspace_id:
        logger.warning(
            "Workspace access denied",
            user_id=current_user.user_id,
            requested_workspace=workspace_id,
            user_workspace=current_user.workspace_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this workspace",
        )


async def validate_upload_ownership(
    upload_id: str,
    current_user: CurrentUser,
    db: AsyncSession,
):
    """
    Validate that current user owns the upload.

    Args:
        upload_id: Upload ID to check
        current_user: Authenticated user
        db: Database session

    Returns:
        Upload object if validation passes

    Raises:
        HTTPException: If upload not found or access denied
    """
    result = await db.execute(select(Upload).where(Upload.id == upload_id))
    upload = result.scalar_one_or_none()

    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found",
        )

    # Check workspace isolation
    if upload.workspace_id != current_user.workspace_id:
        logger.warning(
            "Upload access denied",
            user_id=current_user.user_id,
            upload_id=upload_id,
            upload_workspace=upload.workspace_id,
            user_workspace=current_user.workspace_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this upload",
        )

    return upload


async def validate_asset_ownership(
    asset_id: str,
    current_user: CurrentUser,
    db: AsyncSession,
):
    """
    Validate that current user owns the asset.

    Args:
        asset_id: Asset ID to check
        current_user: Authenticated user
        db: Database session

    Returns:
        Asset object if validation passes

    Raises:
        HTTPException: If asset not found or access denied
    """
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    # Check workspace isolation
    if asset.workspace_id != current_user.workspace_id:
        logger.warning(
            "Asset access denied",
            user_id=current_user.user_id,
            asset_id=asset_id,
            asset_workspace=asset.workspace_id,
            user_workspace=current_user.workspace_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this asset",
        )

    return asset
