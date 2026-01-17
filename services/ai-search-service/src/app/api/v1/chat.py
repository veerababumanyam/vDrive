"""API endpoints for RAG-powered photo chat."""

from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.database import get_db
from ...schemas import (
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
from ...services.rag_service import rag_service

logger = structlog.get_logger()
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="Optional user ID"),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Send a chat message and get an AI-powered response.

    The response includes:
    - Natural language answer based on your photo library
    - Relevant photos found via semantic search
    - Conversation context for follow-up questions

    Example queries:
    - "Show me photos from last summer's wedding"
    - "What events did I shoot in December?"
    - "Find photos with the bride and groom"
    - "Show me my best sunset shots"

    If no conversation_id is provided, a new conversation is created.
    """
    try:
        # Get or create conversation
        if request.conversation_id:
            conversation = await rag_service.get_conversation(
                db=db,
                conversation_id=request.conversation_id,
                workspace_id=workspace_id,
            )
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found",
                )
        else:
            # Create new conversation
            conversation = await rag_service.create_conversation(
                db=db,
                workspace_id=workspace_id,
                user_id=user_id,
            )

        # Process chat message
        result = await rag_service.chat(
            db=db,
            conversation_id=conversation.id,
            workspace_id=workspace_id,
            user_message=request.message,
        )

        await db.commit()

        return ChatResponse(
            response=result["response"],
            conversation_id=UUID(result["conversation_id"]),
            photos=[
                PhotoReference(
                    asset_id=UUID(p["asset_id"]),
                    similarity=p.get("similarity", 0),
                    image_description=p.get("image_description"),
                )
                for p in result.get("photos", [])
            ],
            message_count=result["message_count"],
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail="Chat request failed")


@router.post("/conversations", response_model=CreateConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="Optional user ID"),
    db: AsyncSession = Depends(get_db),
) -> CreateConversationResponse:
    """
    Create a new conversation.

    Conversations persist chat history for multi-turn interactions.
    """
    try:
        conversation = await rag_service.create_conversation(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            title=request.title,
        )

        await db.commit()

        return CreateConversationResponse(
            conversation_id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
        )

    except Exception as e:
        logger.error("Create conversation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    workspace_id: UUID = Query(..., description="Workspace ID"),
    user_id: UUID = Query(None, description="Filter by user ID"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """
    List conversations for a workspace.

    Returns conversations ordered by most recent activity.
    """
    try:
        conversations = await rag_service.list_conversations(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

        return ConversationListResponse(
            conversations=[
                ConversationSummary(
                    id=c.id,
                    title=c.title,
                    message_count=c.message_count,
                    last_activity_at=c.last_activity_at,
                    created_at=c.created_at,
                )
                for c in conversations
            ],
            total=len(conversations),
        )

    except Exception as e:
        logger.error("List conversations failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list conversations")


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail:
    """
    Get conversation details including full message history.
    """
    try:
        conversation = await rag_service.get_conversation(
            db=db,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            message_count=conversation.message_count,
            last_activity_at=conversation.last_activity_at,
            created_at=conversation.created_at,
            messages=[
                ChatMessage(
                    role=m.get("role", "unknown"),
                    content=m.get("content", ""),
                    timestamp=datetime.fromisoformat(m["timestamp"])
                    if m.get("timestamp")
                    else None,
                    photos=m.get("photos"),
                )
                for m in conversation.messages
            ],
            referenced_photos=conversation.referenced_photos,
            status=conversation.status,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Get conversation failed",
            conversation_id=str(conversation_id),
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to get conversation")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Delete a conversation (soft delete).
    """
    try:
        deleted = await rag_service.delete_conversation(
            db=db,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
        )

        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")

        await db.commit()

        return {"deleted": True, "conversation_id": str(conversation_id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Delete conversation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete conversation")


@router.post("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: UUID,
    workspace_id: UUID = Query(..., description="Workspace ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Archive a conversation.
    """
    try:
        archived = await rag_service.archive_conversation(
            db=db,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
        )

        if not archived:
            raise HTTPException(status_code=404, detail="Conversation not found")

        await db.commit()

        return {"archived": True, "conversation_id": str(conversation_id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Archive conversation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to archive conversation")
