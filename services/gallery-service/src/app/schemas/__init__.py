"""Pydantic schemas for Gallery Service API."""

from src.app.schemas.gallery import (
    GalleryResponse,
    GallerySettings,
    GalleryStats,
    GalleryWithSubGalleries,
    PaginatedGalleryResponse,
    PaginationCursor,
    SubGalleryResponse,
    VerifyLinkRequest,
    VerifyLinkResponse,
)
from src.app.schemas.gallery_asset import (
    AssetInteractionRequest,
    AssetInteractionResponse,
    AssetStats,
    GalleryAssetResponse,
    PaginatedGalleryAssetResponse,
    VerifyPinRequest,
    VerifyPinResponse,
)

__all__ = [
    # Gallery schemas
    "GalleryResponse",
    "GallerySettings",
    "GalleryStats",
    "GalleryWithSubGalleries",
    "SubGalleryResponse",
    "VerifyLinkRequest",
    "VerifyLinkResponse",
    "PaginatedGalleryResponse",
    "PaginationCursor",
    # Gallery Asset schemas
    "GalleryAssetResponse",
    "AssetStats",
    "VerifyPinRequest",
    "VerifyPinResponse",
    "AssetInteractionRequest",
    "AssetInteractionResponse",
    "PaginatedGalleryAssetResponse",
]
