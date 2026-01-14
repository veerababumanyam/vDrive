"""Public access API endpoints for magic link gallery viewing."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.auth import create_gallery_access_token
from src.app.core.database import get_db
from src.app.core.logging import logger
from src.app.schemas.gallery import (
    GalleryResponse,
    PaginationCursor,
    VerifyLinkRequest,
    VerifyLinkResponse,
)
from src.app.schemas.gallery_asset import (
    GalleryAssetResponse,
    PaginatedGalleryAssetResponse,
    VerifyPinRequest,
    VerifyPinResponse,
)
from src.app.services.gallery_service import GalleryService
from src.app.services.security_audit_service import SecurityAuditService
from src.app.services.share_link_service import ShareLinkService
from src.app.services.signed_url_service import get_signed_url_service
from src.app.utils.security import verify_password

router = APIRouter()


@router.post(
    "/verify-link",
    response_model=VerifyLinkResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify magic link",
    description="Verify a magic link and return access token if valid",
)
async def verify_magic_link(
    body: VerifyLinkRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> VerifyLinkResponse:
    """Verify a magic link and return gallery access token.

    Frontend flow:
    1. User clicks magic link (contains link_id in URL)
    2. Frontend calls this endpoint with link_id
    3. If password_required error, show password form
    4. If successful, store access_token and navigate to gallery
    """
    # Verify link and password
    is_valid, share_link, error_code = await ShareLinkService.verify_link(
        link_id=body.link_id,
        password=body.password,
        db=db,
    )

    if not is_valid:
        # Log failed access attempt
        gallery_id = share_link.gallery_id if share_link else None
        if gallery_id:
            await SecurityAuditService.log_link_access(
                link_id=body.link_id,
                gallery_id=gallery_id,
                result="failure",
                db=db,
                request=request,
                error=error_code,
            )

        error_messages = {
            "invalid_link": "This link is invalid or does not exist",
            "expired": "This link has expired",
            "password_required": "This gallery requires a password",
            "invalid_password": "Incorrect password",
        }

        return VerifyLinkResponse(
            access_granted=False,
            error=error_code,
            message=error_messages.get(error_code, "Access denied"),
        )

    # Load gallery
    gallery = await GalleryService.get_by_id(
        gallery_id=share_link.gallery_id,
        db=db,
    )

    if not gallery:
        logger.error(
            "Gallery not found for valid share link",
            link_id=body.link_id,
            gallery_id=share_link.gallery_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gallery configuration error",
        )

    # Log successful access
    await SecurityAuditService.log_link_access(
        link_id=body.link_id,
        gallery_id=gallery.id,
        result="success",
        db=db,
        request=request,
    )

    # Increment access count
    await ShareLinkService.increment_access_count(share_link, db)

    # Generate JWT token for gallery access
    access_token = create_gallery_access_token(
        gallery_id=gallery.id,
        link_id=share_link.link_id,
    )

    # Return success response
    return VerifyLinkResponse(
        access_granted=True,
        access_token=access_token,
        gallery=GalleryResponse.model_validate(gallery),
    )


@router.get(
    "/gallery/{gallery_id}/photos",
    response_model=PaginatedGalleryAssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get gallery photos",
    description="Get paginated list of photos in a gallery",
)
async def get_gallery_photos(
    gallery_id: str,
    sub_gallery_id: Optional[str] = Query(None, description="Filter by sub-gallery"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedGalleryAssetResponse:
    """Get paginated gallery photos with signed URLs.

    Frontend implementation:
    - Use for infinite scroll or "Load More" pagination
    - Pass cursor from previous response to get next page
    - When next_cursor is null, you've reached the end

    Note: This endpoint should be protected by JWT middleware in production.
    For now, it's open for demonstration purposes.
    """
    # Verify gallery exists
    gallery = await GalleryService.get_by_id(gallery_id, db)
    if not gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found",
        )

    # Get paginated assets
    assets, next_cursor, has_more = await GalleryService.get_gallery_assets(
        gallery_id=gallery_id,
        sub_gallery_id=sub_gallery_id,
        limit=limit,
        cursor=cursor,
        db=db,
    )

    # Generate signed URLs for each asset
    signed_url_service = get_signed_url_service()
    asset_responses = []

    for asset in assets:
        # TODO: Get actual object keys from asset-service
        # For now, use placeholder logic
        original_key = f"assets/{asset.asset_id}/original.jpg"
        thumbnail_key = f"assets/{asset.asset_id}/thumbnail.jpg"
        lqip_key = f"assets/{asset.asset_id}/lqip.jpg"

        # Generate URLs (only for non-private assets)
        urls = {"asset_url": None, "thumbnail_url": None, "lqip_url": None}
        if not asset.is_private:
            try:
                urls = signed_url_service.generate_asset_urls(
                    asset_id=asset.asset_id,
                    original_key=original_key,
                    thumbnail_key=thumbnail_key,
                    lqip_key=lqip_key,
                    expires_in=3600,
                )
            except Exception as e:
                logger.error(
                    "Failed to generate signed URLs",
                    asset_id=asset.asset_id,
                    error=str(e),
                )
                # Continue with None URLs

        # Build response
        asset_dict = asset.to_dict(include_asset_url=True)
        asset_dict.update(urls)

        asset_responses.append(GalleryAssetResponse.model_validate(asset_dict))

    return PaginatedGalleryAssetResponse(
        data=asset_responses,
        pagination=PaginationCursor(
            next_cursor=next_cursor,
            has_more=has_more,
        ),
    )


@router.post(
    "/photo/{asset_id}/verify-pin",
    response_model=VerifyPinResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify PIN for private photo",
    description="Verify PIN and return signed URL for private photo",
)
async def verify_photo_pin(
    asset_id: str,
    body: VerifyPinRequest,
    http_request: Request,
    gallery_id: str = Query(..., description="Gallery ID (for security)"),
    db: AsyncSession = Depends(get_db),
) -> VerifyPinResponse:
    """Verify PIN for private photo access.

    Frontend flow:
    1. User clicks on private photo (is_private: true, has_pin: true)
    2. Show PIN input modal
    3. Call this endpoint with PIN
    4. If successful, display photo with signed URL
    5. If failed, show error and allow retry (with rate limiting)
    """
    # Get asset
    asset = await GalleryService.get_asset_by_id(
        asset_id=asset_id,
        gallery_id=gallery_id,
        db=db,
    )

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )

    # Check if asset is actually private
    if not asset.is_private or not asset.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This photo is not PIN-protected",
        )

    # Verify PIN
    pin_valid = verify_password(asset.pin_hash, body.pin)

    # Log PIN attempt
    await SecurityAuditService.log_pin_attempt(
        asset_id=asset_id,
        gallery_id=gallery_id,
        success=pin_valid,
        db=db,
        request=http_request,
    )

    if not pin_valid:
        logger.warning(
            "Invalid PIN attempt",
            asset_id=asset_id,
            gallery_id=gallery_id,
        )
        return VerifyPinResponse(
            access_granted=False,
            error="invalid_pin",
            message="Incorrect PIN. Please try again.",
        )

    # Generate signed URL for the asset
    signed_url_service = get_signed_url_service()

    # TODO: Get actual object key from asset-service
    original_key = f"assets/{asset.asset_id}/original.jpg"

    try:
        urls = signed_url_service.generate_asset_urls(
            asset_id=asset.asset_id,
            original_key=original_key,
            expires_in=3600,
        )

        return VerifyPinResponse(
            access_granted=True,
            asset_url=urls["asset_url"],
        )

    except Exception as e:
        logger.error(
            "Failed to generate signed URL for private asset",
            asset_id=asset_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate access URL",
        )
