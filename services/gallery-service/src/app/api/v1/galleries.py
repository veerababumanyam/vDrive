"""Gallery CRUD API endpoints (authenticated staff routes)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.auth import CurrentUser, get_current_user
from src.app.core.database import get_db
from src.app.core.logging import logger
from src.app.schemas.gallery_crud import (
    GalleryCreateRequest,
    GalleryListItem,
    GalleryListResponse,
    GalleryUpdateRequest,
)
from src.app.schemas.gallery_asset import PaginatedGalleryAssetResponse
from src.app.schemas.share_link import ShareLinkCreate, ShareLinkResponse
from src.app.services.gallery_service import GalleryService
from src.app.services.share_link_service import ShareLinkService

router = APIRouter(prefix="/galleries", tags=["Galleries"])


def _gallery_to_response(gallery) -> dict:
    """Convert Gallery model to API response dict matching frontend types."""
    return {
        "gallery_id": gallery.id,
        "workspace_id": gallery.workspace_id,
        "title": gallery.title,
        "description": gallery.description,
        "client_name": gallery.client_name,
        "shoot_date": gallery.shoot_date.isoformat() if gallery.shoot_date else None,
        "status": gallery.status,
        "cover_asset_id": gallery.cover_asset_id,
        "cover_url": None,  # TODO: Generate signed URL if cover exists
        # Settings
        "password_protected": gallery.password_protected,
        "pin_protected": gallery.pin_protected,
        "email_registration_required": gallery.email_registration_required,
        "download_policy": gallery.download_policy,
        "layout_style": gallery.layout_style,
        "theme": gallery.theme,
        # Stats
        "photo_count": gallery.photo_count,
        "video_count": gallery.video_count,
        "favorites_count": gallery.favorites_count,
        "total_size_bytes": gallery.total_size_bytes,
        # Timestamps
        "created_at": gallery.created_at.isoformat() if gallery.created_at else None,
        "updated_at": gallery.updated_at.isoformat() if gallery.updated_at else None,
    }


@router.get(
    "",
    response_model=GalleryListResponse,
    summary="List galleries",
    description="List all galleries for the current workspace with pagination",
)
async def list_galleries(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status", alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GalleryListResponse:
    """List galleries for authenticated user's workspace."""
    if not current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No workspace selected",
        )

    galleries, total = await GalleryService.list_galleries(
        workspace_id=current_user.workspace_id,
        db=db,
        status=status_filter,
        page=page,
        page_size=page_size,
    )

    return GalleryListResponse(
        galleries=[GalleryListItem(**_gallery_to_response(g)) for g in galleries],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create gallery",
    description="Create a new gallery in the current workspace",
)
async def create_gallery(
    request: GalleryCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create new gallery."""
    if not current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No workspace selected",
        )

    logger.info(
        "Creating gallery",
        workspace_id=current_user.workspace_id,
        user_id=current_user.user_id,
        title=request.title,
    )

    gallery = await GalleryService.create_gallery(
        workspace_id=current_user.workspace_id,
        data=request,
        db=db,
    )

    return _gallery_to_response(gallery)


@router.get(
    "/{gallery_id}",
    summary="Get gallery",
    description="Get single gallery details by ID",
)
async def get_gallery(
    gallery_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get gallery by ID with ownership verification."""
    gallery = await GalleryService.get_by_id(
        gallery_id, db, include_sub_galleries=True
    )

    if not gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found",
        )

    if gallery.workspace_id != current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    response = _gallery_to_response(gallery)
    # Include sub-galleries
    if gallery.sub_galleries:
        response["sub_galleries"] = [
            {
                "sub_gallery_id": sg.id,
                "gallery_id": sg.gallery_id,
                "name": sg.name,
                "sort_order": sg.sort_order,
                "visible": sg.visible,
                "cover_asset_id": sg.cover_asset_id,
                "cover_url": None,
                "photo_count": sg.photo_count,
            }
            for sg in gallery.sub_galleries
        ]

    return response


@router.patch(
    "/{gallery_id}",
    summary="Update gallery",
    description="Update gallery details",
)
async def update_gallery(
    gallery_id: str,
    request: GalleryUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update gallery."""
    gallery = await GalleryService.update_gallery(
        gallery_id=gallery_id,
        workspace_id=current_user.workspace_id,
        data=request,
        db=db,
    )

    if not gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found or access denied",
        )

    return _gallery_to_response(gallery)


@router.delete(
    "/{gallery_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete gallery",
    description="Delete a gallery",
)
async def delete_gallery(
    gallery_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete gallery."""
    deleted = await GalleryService.delete_gallery(
        gallery_id=gallery_id,
        workspace_id=current_user.workspace_id,
        db=db,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found or access denied",
        )


@router.post(
    "/{gallery_id}/publish",
    summary="Publish gallery",
    description="Change gallery status to published",
)
async def publish_gallery(
    gallery_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Publish gallery."""
    update = GalleryUpdateRequest(status="published")
    gallery = await GalleryService.update_gallery(
        gallery_id=gallery_id,
        workspace_id=current_user.workspace_id,
        data=update,
        db=db,
    )

    if not gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found or access denied",
        )

    return _gallery_to_response(gallery)


@router.post(
    "/{gallery_id}/archive",
    summary="Archive gallery",
    description="Change gallery status to archived",
)
async def archive_gallery(
    gallery_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Archive gallery."""
    update = GalleryUpdateRequest(status="archived")
    gallery = await GalleryService.update_gallery(
        gallery_id=gallery_id,
        workspace_id=current_user.workspace_id,
        data=update,
        db=db,
    )

    if not gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found or access denied",
        )

    return _gallery_to_response(gallery)


@router.get(
    "/{gallery_id}/photos",
    response_model=PaginatedGalleryAssetResponse,
    summary="Get gallery photos",
    description="Get photos for a gallery (staff view includes private)",
)
async def get_gallery_photos(
    gallery_id: str,
    cursor: Optional[str] = None,
    limit: int = 50,
    sub_gallery_id: Optional[str] = None,
    include_private: bool = True,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedGalleryAssetResponse:
    """Get gallery photos."""
    # Verify access
    gallery = await GalleryService.get_by_id(gallery_id, db)
    if not gallery or gallery.workspace_id != current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found",
        )

    assets, next_cursor, has_more = await GalleryService.get_gallery_assets(
        gallery_id=gallery_id,
        db=db,
        sub_gallery_id=sub_gallery_id,
        limit=limit,
        cursor=cursor,
    )

    from src.app.schemas.gallery import PaginationCursor

    return PaginatedGalleryAssetResponse(
        data=assets,
        pagination=PaginationCursor(
            cursor=next_cursor,
            has_more=has_more,
            limit=limit,
            total=0,  # Total count expensive to calculate
        ),
    )


@router.get(
    "/{gallery_id}/share-links",
    response_model=list[ShareLinkResponse],
    summary="List share links",
    description="List all share links for a gallery",
)
async def list_share_links(
    gallery_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ShareLinkResponse]:
    """List share links."""
    # Verify access
    gallery = await GalleryService.get_by_id(gallery_id, db)
    if not gallery or gallery.workspace_id != current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found",
        )

    links = await ShareLinkService.list_links(gallery_id, db)
    # Pydantic will handle conversion from ORM models
    return links  # type: ignore


@router.post(
    "/{gallery_id}/share-links",
    response_model=ShareLinkResponse,
    summary="Create share link",
    description="Create a new share link",
)
async def create_share_link(
    gallery_id: str,
    request: ShareLinkCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareLinkResponse:
    """Create share link."""
    # Verify access
    gallery = await GalleryService.get_by_id(gallery_id, db)
    if not gallery or gallery.workspace_id != current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found",
        )

    link = await ShareLinkService.create_link(
        gallery_id=gallery_id,
        data=request,
        created_by_id=current_user.user_id,
        db=db,
    )
    return link  # type: ignore


@router.delete(
    "/{gallery_id}/share-links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke share link",
    description="Revoke a share link",
)
async def revoke_share_link(
    gallery_id: str,
    link_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke share link."""
    # Verify access
    gallery = await GalleryService.get_by_id(gallery_id, db)
    if not gallery or gallery.workspace_id != current_user.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found",
        )

    revoked = await ShareLinkService.revoke_link(link_id, gallery_id, db)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found",
        )
