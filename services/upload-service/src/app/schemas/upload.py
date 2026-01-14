"""Upload schemas for TUS protocol."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

ALLOWED_MIME_TYPES = [
    "image/jpeg", "image/png", "image/webp", "image/heic",
    "image/x-canon-cr2", "image/x-nikon-nef", "image/x-sony-arw", "image/x-adobe-dng",
    "video/mp4", "video/quicktime", "video/x-msvideo"
]

class CreateUploadRequest(BaseModel):
    filename: str = Field(..., max_length=255)
    mime_type: str
    expected_size: int = Field(..., gt=0, le=10737418240)
    workspace_id: str
    gallery_id: Optional[str] = None
    checksum: Optional[str] = Field(None, min_length=64, max_length=64)

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        if v not in ALLOWED_MIME_TYPES:
            raise ValueError(f"MIME type {v} not allowed")
        return v

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        if "/" in v or "\\" in v or v.startswith("."):
            raise ValueError("Invalid filename")
        return v

class CreateUploadResponse(BaseModel):
    upload_id: str
    upload_url: str
    expires_at: datetime

class UploadStatusResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    expected_size: int
    received_bytes: int
    progress_percent: float
    status: str
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

class TUSHeaders(BaseModel):
    tus_resumable: str = "1.0.0"
    upload_offset: Optional[int] = None
    upload_length: Optional[int] = None

class ListUploadsResponse(BaseModel):
    uploads: list[UploadStatusResponse]
    total: int
    cursor: Optional[str] = None
