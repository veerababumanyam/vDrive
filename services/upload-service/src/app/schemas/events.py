"""Kafka event schemas."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field

class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "upload-service"
    version: str = "1.0"

class UploadInitiatedEvent(BaseEvent):
    event_type: str = "upload.initiated"
    upload_id: str
    workspace_id: str
    filename: str
    expected_size: int

class UploadCompletedEvent(BaseEvent):
    event_type: str = "upload.completed"
    upload_id: str
    workspace_id: str
    asset_id: str
    filename: str
    mime_type: str
    file_size: int
    storage_path: str
    checksum: str
    is_encrypted: bool
    encryption_key_id: Optional[str] = None

class UploadFailedEvent(BaseEvent):
    event_type: str = "upload.failed"
    upload_id: str
    workspace_id: str
    error_code: str
    error_message: str
    retry_count: int

class AssetProcessingEvent(BaseEvent):
    event_type: str = "asset.processing"
    asset_id: str
    workspace_id: str
    tasks: list[str]  # thumbnail_generation, exif_extraction, face_detection
    priority: int = 5

class AssetProcessedEvent(BaseEvent):
    event_type: str = "asset.processed"
    asset_id: str
    workspace_id: str
    thumbnail_key: Optional[str] = None
    preview_key: Optional[str] = None
    lqip_base64: Optional[str] = None
    has_metadata: bool = False
    faces_detected: int = 0

class FaceDetectedEvent(BaseEvent):
    event_type: str = "face.detected"
    face_id: str
    asset_id: str
    workspace_id: str
    bounding_box: dict
    confidence: float
