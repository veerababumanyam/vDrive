"""Pydantic schemas for AI Search service API."""

from .caption import (
    CaptionRequest,
    CaptionResponse,
    CaptionSuggestion,
    DetectedContext,
    RegenerateCaptionRequest,
    SelectCaptionRequest,
)
from .chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationListResponse,
    ConversationSummary,
    CreateConversationRequest,
    CreateConversationResponse,
    PhotoReference,
)
from .search import (
    EmbeddingStatus,
    SearchQuery,
    SearchResponse,
    SearchResult,
    SearchStats,
    SimilarPhotosRequest,
    SimilarPhotosResponse,
)

__all__ = [
    # Caption schemas
    "CaptionRequest",
    "CaptionResponse",
    "CaptionSuggestion",
    "DetectedContext",
    "RegenerateCaptionRequest",
    "SelectCaptionRequest",
    # Chat schemas
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ConversationDetail",
    "ConversationListResponse",
    "ConversationSummary",
    "CreateConversationRequest",
    "CreateConversationResponse",
    "PhotoReference",
    # Search schemas
    "EmbeddingStatus",
    "SearchQuery",
    "SearchResponse",
    "SearchResult",
    "SearchStats",
    "SimilarPhotosRequest",
    "SimilarPhotosResponse",
]
