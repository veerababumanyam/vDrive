"""Pydantic schemas for RAG chat API."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationStatus(str, Enum):
    """Conversation status states."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ChatMessage(BaseModel):
    """A single chat message."""

    role: str = Field(
        ...,
        description="Message role: user, assistant, or system",
    )
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")
    photos: Optional[list[str]] = Field(
        None,
        description="Asset IDs of referenced photos",
    )


class ChatRequest(BaseModel):
    """Request schema for chat message."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's message",
    )
    conversation_id: Optional[UUID] = Field(
        None,
        description="Existing conversation ID (creates new if not provided)",
    )


class PhotoReference(BaseModel):
    """Photo reference in chat response."""

    asset_id: UUID = Field(..., description="Asset ID")
    similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score",
    )
    image_description: Optional[str] = Field(
        None,
        description="AI-generated description",
    )


class ChatResponse(BaseModel):
    """Response schema for chat message."""

    response: str = Field(..., description="Assistant's response")
    conversation_id: UUID = Field(..., description="Conversation ID")
    photos: list[PhotoReference] = Field(
        default=[],
        description="Relevant photos found",
    )
    message_count: int = Field(..., description="Total messages in conversation")


class ConversationSummary(BaseModel):
    """Summary of a conversation for listing."""

    id: UUID = Field(..., description="Conversation ID")
    title: Optional[str] = Field(None, description="Conversation title")
    message_count: int = Field(..., description="Number of messages")
    last_activity_at: datetime = Field(..., description="Last activity timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")


class ConversationDetail(ConversationSummary):
    """Detailed conversation with messages."""

    messages: list[ChatMessage] = Field(
        default=[],
        description="Conversation messages",
    )
    referenced_photos: list[str] = Field(
        default=[],
        description="All photos referenced in conversation",
    )
    status: ConversationStatus = Field(..., description="Conversation status")


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""

    conversations: list[ConversationSummary] = Field(
        default=[],
        description="List of conversations",
    )
    total: int = Field(..., description="Total conversations")


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""

    title: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional conversation title",
    )


class CreateConversationResponse(BaseModel):
    """Response after creating a conversation."""

    conversation_id: UUID = Field(..., description="New conversation ID")
    title: Optional[str] = Field(None, description="Conversation title")
    created_at: datetime = Field(..., description="Creation timestamp")
