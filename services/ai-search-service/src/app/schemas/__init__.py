"""Pydantic schemas for AI Search service API."""

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
