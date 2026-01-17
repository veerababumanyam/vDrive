"""Pydantic schemas for face service API."""

from .face import (
    BoundingBox,
    FaceCreate,
    FaceResponse,
    FaceGroupCreate,
    FaceGroupUpdate,
    FaceGroupResponse,
    FaceGroupDetailResponse,
    FacesListResponse,
    PeopleListResponse,
    PhotosForPersonResponse,
)
from .people import (
    MergeRequest,
    MergeResponse,
    SplitRequest,
    SplitResponse,
    GroupNameUpdate,
    FindMeMatch,
    FindMeResponse,
)

__all__ = [
    "BoundingBox",
    "FaceCreate",
    "FaceResponse",
    "FaceGroupCreate",
    "FaceGroupUpdate",
    "FaceGroupResponse",
    "FaceGroupDetailResponse",
    "FacesListResponse",
    "PeopleListResponse",
    "PhotosForPersonResponse",
    "MergeRequest",
    "MergeResponse",
    "SplitRequest",
    "SplitResponse",
    "GroupNameUpdate",
    "FindMeMatch",
    "FindMeResponse",
]
