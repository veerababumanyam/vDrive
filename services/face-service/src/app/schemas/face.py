"""Pydantic schemas for face detection API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Normalized bounding box coordinates."""

    x: float = Field(..., ge=0, le=1, description="Left coordinate (0-1)")
    y: float = Field(..., ge=0, le=1, description="Top coordinate (0-1)")
    width: float = Field(..., ge=0, le=1, description="Width (0-1)")
    height: float = Field(..., ge=0, le=1, description="Height (0-1)")


class FaceBase(BaseModel):
    """Base schema for face data."""

    bounding_box: BoundingBox
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")


class FaceCreate(FaceBase):
    """Schema for creating a face (internal use)."""

    asset_id: UUID
    workspace_id: UUID
    landmarks: Optional[dict[str, list[float]]] = None
    detection_metadata: Optional[dict] = None


class FaceResponse(FaceBase):
    """Schema for face API responses."""

    id: UUID
    asset_id: UUID
    group_id: Optional[UUID] = None
    landmarks: Optional[dict[str, list[float]]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FaceGroupBase(BaseModel):
    """Base schema for face group data."""

    name: Optional[str] = Field(None, max_length=255, description="Person name")


class FaceGroupCreate(FaceGroupBase):
    """Schema for creating a face group."""

    workspace_id: UUID


class FaceGroupUpdate(BaseModel):
    """Schema for updating a face group."""

    name: Optional[str] = Field(None, max_length=255)


class FaceGroupResponse(FaceGroupBase):
    """Schema for face group API responses."""

    id: UUID
    workspace_id: UUID
    representative_face_id: Optional[UUID] = None
    face_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FaceGroupDetailResponse(FaceGroupResponse):
    """Detailed face group response with faces."""

    faces: list[FaceResponse] = []


class FacesListResponse(BaseModel):
    """Response for listing faces."""

    faces: list[FaceResponse]
    total: int


class PeopleListResponse(BaseModel):
    """Response for listing people (face groups)."""

    people: list[FaceGroupResponse]
    total: int


class PhotosForPersonResponse(BaseModel):
    """Response for photos containing a specific person."""

    person: FaceGroupResponse
    photos: list[dict]  # Contains asset_id, thumbnail_url, face bounding_box
    total: int
