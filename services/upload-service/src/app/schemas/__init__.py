"""Pydantic schemas for Upload Service API."""

from .upload import (
    CreateUploadRequest,
    CreateUploadResponse,
    UploadStatusResponse,
    ListUploadsResponse,
    TUSHeaders,
)
from .asset import (
    AssetResponse,
    AssetMetadataResponse,
    AssetURLs,
    AssetProcessingResponse,
    ProcessingTaskResponse,
)
from .events import (
    BaseEvent,
    UploadInitiatedEvent,
    UploadCompletedEvent,
    UploadFailedEvent,
    AssetProcessingEvent,
    AssetProcessedEvent,
    FaceDetectedEvent,
)

__all__ = [
    # Upload schemas
    "CreateUploadRequest",
    "CreateUploadResponse",
    "UploadStatusResponse",
    "ListUploadsResponse",
    "TUSHeaders",
    # Asset schemas
    "AssetResponse",
    "AssetMetadataResponse",
    "AssetURLs",
    "AssetProcessingResponse",
    "ProcessingTaskResponse",
    # Event schemas
    "BaseEvent",
    "UploadInitiatedEvent",
    "UploadCompletedEvent",
    "UploadFailedEvent",
    "AssetProcessingEvent",
    "AssetProcessedEvent",
    "FaceDetectedEvent",
]
