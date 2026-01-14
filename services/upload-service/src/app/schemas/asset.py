"""Asset schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AssetURLs(BaseModel):
    original: str
    thumbnail: Optional[str] = None
    preview: Optional[str] = None
    lqip: Optional[str] = None

class AssetMetadataResponse(BaseModel):
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    iso: Optional[int] = None
    aperture: Optional[float] = None
    shutter_speed: Optional[str] = None
    focal_length: Optional[float] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    captured_at: Optional[datetime] = None

class ProcessingTaskResponse(BaseModel):
    task_type: str
    status: str
    error_message: Optional[str] = None

class AssetProcessingResponse(BaseModel):
    overall_status: str
    tasks: list[ProcessingTaskResponse]

class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    is_encrypted: bool
    processing_status: str
    urls: Optional[AssetURLs] = None
    metadata: Optional[AssetMetadataResponse] = None
    faces_count: int = 0
    created_at: datetime
    updated_at: datetime
