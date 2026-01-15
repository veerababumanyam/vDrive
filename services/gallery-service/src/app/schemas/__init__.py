"""Pydantic schemas for Gallery Service API."""

from src.app.schemas.batch import (
    BATCH_OPERATIONS,
    BatchError,
    BatchOperationSummary,
    BatchOperationType,
    BatchRequest,
    BatchResponse,
    BatchStatusResponse,
)
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
from src.app.schemas.preview import (
    PreviewRequest,
    PreviewSessionResponse,
    PreviewStatusResponse,
    PreviewToggleResponse,
    ValidatePreviewTokenRequest,
    ValidatePreviewTokenResponse,
)
from src.app.schemas.websocket import (
    ConnectionInfo,
    ErrorData,
    GalleryUpdatedData,
    MagicLinkAuth,
    PhotoAddedData,
    PhotoRemovedData,
    WebSocketAuthResponse,
    WebSocketMessage,
    WebSocketMessageType,
)

__all__ = [
    # Batch schemas
    "BATCH_OPERATIONS",
    "BatchError",
    "BatchOperationSummary",
    "BatchOperationType",
    "BatchRequest",
    "BatchResponse",
    "BatchStatusResponse",
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
    # Preview schemas
    "PreviewRequest",
    "PreviewSessionResponse",
    "PreviewStatusResponse",
    "PreviewToggleResponse",
    "ValidatePreviewTokenRequest",
    "ValidatePreviewTokenResponse",
    # WebSocket schemas
    "ConnectionInfo",
    "ErrorData",
    "GalleryUpdatedData",
    "MagicLinkAuth",
    "PhotoAddedData",
    "PhotoRemovedData",
    "WebSocketAuthResponse",
    "WebSocketMessage",
    "WebSocketMessageType",
]
