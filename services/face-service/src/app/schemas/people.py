"""Pydantic schemas for people management API."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MergeRequest(BaseModel):
    """Request to merge multiple face groups into one."""

    source_group_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="Groups to merge from",
    )
    target_group_id: UUID = Field(..., description="Group to merge into")


class MergeResponse(BaseModel):
    """Response from merge operation."""

    merged: int = Field(..., description="Number of groups merged")
    faces_moved: int = Field(..., description="Number of faces moved")
    target_group_id: UUID


class SplitRequest(BaseModel):
    """Request to split faces from a group into a new group."""

    group_id: UUID = Field(..., description="Group to split from")
    face_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="Face IDs to move to new group",
    )


class SplitResponse(BaseModel):
    """Response from split operation."""

    new_group_id: UUID = Field(..., description="ID of newly created group")
    faces_moved: int = Field(..., description="Number of faces moved")
    remaining_in_original: int = Field(..., description="Faces remaining in original group")


class GroupNameUpdate(BaseModel):
    """Request to update a group's name."""

    name: Optional[str] = Field(None, max_length=255, description="New name for the person")


class FindMeRequest(BaseModel):
    """Request for Find Me (selfie matching) feature."""

    # Image will be uploaded as multipart/form-data
    # This schema is for the response
    pass


class FindMeMatch(BaseModel):
    """A single match from Find Me search."""

    asset_id: UUID
    face_id: UUID
    group_id: Optional[UUID] = None
    similarity: float = Field(..., ge=0, le=1, description="Similarity score")
    bounding_box: dict[str, float]


class FindMeResponse(BaseModel):
    """Response from Find Me search."""

    matches: list[FindMeMatch]
    total: int
    person_group_id: Optional[UUID] = Field(
        None,
        description="If matches found, the person's group ID",
    )
