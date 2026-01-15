"""RAG (Retrieval-Augmented Generation) service for photo chat."""

from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.llm import generate_chat_response
from ..models import Conversation, ConversationStatus
from .search_service import search_service

logger = structlog.get_logger()

# System prompt for photo-aware chat
SYSTEM_PROMPT = """You are a helpful AI assistant for a photography platform called vDrive.
You help photographers search, organize, and understand their photo libraries.

When answering questions:
1. Base your answers on the photos found in the user's library
2. Reference specific photos when relevant (use asset IDs)
3. Be concise but informative
4. If no relevant photos are found, explain that clearly
5. Help users discover patterns in their photo collection

You have access to semantic search to find relevant photos based on the user's query.
When photos are found, they will be provided as context for your response.

Current context includes information about photos matching the user's query.
"""


class RAGService:
    """
    RAG service for photo-aware conversational AI.

    Features:
    - Semantic photo retrieval for context
    - Multi-turn conversation support
    - Context compression for long conversations
    - Gemini LLM integration
    """

    async def create_conversation(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
        title: Optional[str] = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: Optional user ID
            title: Optional conversation title

        Returns:
            Created Conversation
        """
        conversation = Conversation(
            workspace_id=workspace_id,
            user_id=user_id,
            title=title,
            messages=[],
            referenced_photos=[],
            status=ConversationStatus.ACTIVE,
        )

        db.add(conversation)
        await db.flush()
        await db.refresh(conversation)

        logger.info(
            "Conversation created",
            conversation_id=str(conversation.id),
            workspace_id=str(workspace_id),
        )

        return conversation

    async def get_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
    ) -> Optional[Conversation]:
        """Get a conversation by ID."""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.workspace_id == workspace_id)
            .where(Conversation.status == ConversationStatus.ACTIVE)
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        user_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Conversation]:
        """List conversations for a workspace."""
        query = (
            select(Conversation)
            .where(Conversation.workspace_id == workspace_id)
            .where(Conversation.status == ConversationStatus.ACTIVE)
            .order_by(Conversation.last_activity_at.desc())
            .offset(offset)
            .limit(limit)
        )

        if user_id:
            query = query.where(Conversation.user_id == user_id)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def chat(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
        user_message: str,
    ) -> dict:
        """
        Process a chat message and generate a response.

        Args:
            db: Database session
            conversation_id: Conversation ID
            workspace_id: Workspace ID
            user_message: User's message

        Returns:
            Dict with response and metadata
        """
        # Get conversation
        conversation = await self.get_conversation(db, conversation_id, workspace_id)
        if not conversation:
            raise ValueError("Conversation not found")

        logger.info(
            "Processing chat message",
            conversation_id=str(conversation_id),
            message_length=len(user_message),
        )

        # Step 1: Retrieve relevant photos using semantic search
        relevant_photos = await self._retrieve_photos(
            db=db,
            query=user_message,
            workspace_id=workspace_id,
        )

        # Step 2: Build context from photos
        photo_context = self._build_photo_context(relevant_photos)

        # Step 3: Build conversation history
        history_context = self._build_history_context(conversation)

        # Step 4: Generate response
        full_prompt = self._build_prompt(
            user_message=user_message,
            photo_context=photo_context,
            history_context=history_context,
        )

        assistant_response = await self._generate_response(full_prompt)

        # Step 5: Update conversation
        photo_ids = [p["asset_id"] for p in relevant_photos]
        conversation.add_message("user", user_message)
        conversation.add_message("assistant", assistant_response, photos=photo_ids)

        # Auto-generate title from first message
        if conversation.message_count == 2 and not conversation.title:
            conversation.title = self._generate_title(user_message)

        await db.flush()

        logger.info(
            "Chat response generated",
            conversation_id=str(conversation_id),
            photos_found=len(relevant_photos),
        )

        return {
            "response": assistant_response,
            "photos": relevant_photos,
            "conversation_id": str(conversation_id),
            "message_count": conversation.message_count,
        }

    async def _retrieve_photos(
        self,
        db: AsyncSession,
        query: str,
        workspace_id: UUID,
        limit: int = None,
    ) -> list[dict]:
        """
        Retrieve relevant photos for the query using semantic search.

        Args:
            db: Database session
            query: Search query
            workspace_id: Workspace ID
            limit: Max photos to retrieve

        Returns:
            List of relevant photos with metadata
        """
        if limit is None:
            limit = settings.RAG_MAX_CONTEXT_PHOTOS

        try:
            results = await search_service.semantic_search(
                db=db,
                query=query,
                workspace_id=workspace_id,
                limit=limit,
                threshold=settings.RAG_SIMILARITY_THRESHOLD,
            )

            return results

        except Exception as e:
            logger.error("Photo retrieval failed", error=str(e))
            return []

    def _build_photo_context(self, photos: list[dict]) -> str:
        """Build context string from retrieved photos."""
        if not photos:
            return "No relevant photos were found for this query."

        context_parts = [f"Found {len(photos)} relevant photos:"]

        for i, photo in enumerate(photos, 1):
            similarity = photo.get("similarity", 0)
            asset_id = photo.get("asset_id", "unknown")
            description = photo.get("image_description", "")

            parts = [f"{i}. Photo ID: {asset_id}"]
            parts.append(f"   Relevance: {similarity:.0%}")
            if description:
                parts.append(f"   Description: {description}")

            context_parts.append("\n".join(parts))

        return "\n\n".join(context_parts)

    def _build_history_context(
        self,
        conversation: Conversation,
        max_messages: int = 10,
    ) -> str:
        """Build context from conversation history."""
        recent = conversation.get_recent_messages(max_messages)

        if not recent:
            return ""

        history_parts = ["Previous conversation:"]

        for msg in recent:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")[:500]  # Truncate long messages
            history_parts.append(f"{role}: {content}")

        return "\n".join(history_parts)

    def _build_prompt(
        self,
        user_message: str,
        photo_context: str,
        history_context: str,
    ) -> str:
        """Build the full prompt for the LLM."""
        prompt_parts = [SYSTEM_PROMPT]

        if history_context:
            prompt_parts.append(history_context)

        prompt_parts.append(f"\nPhoto context:\n{photo_context}")
        prompt_parts.append(f"\nUser: {user_message}")
        prompt_parts.append("\nAssistant:")

        return "\n\n".join(prompt_parts)

    async def _generate_response(self, prompt: str) -> str:
        """Generate response using Gemini."""
        try:
            response = await generate_chat_response(
                messages=[{"role": "user", "content": prompt}]
            )

            if response:
                return response

            return "I apologize, but I couldn't generate a response. Please try again."

        except Exception as e:
            logger.error("Response generation failed", error=str(e))
            return "I encountered an error while processing your request. Please try again."

    def _generate_title(self, first_message: str, max_length: int = 50) -> str:
        """Generate a title from the first message."""
        # Take first sentence or truncate
        title = first_message.split(".")[0].split("?")[0].split("!")[0]
        title = title.strip()

        if len(title) > max_length:
            title = title[: max_length - 3] + "..."

        return title or "New Conversation"

    async def archive_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
    ) -> bool:
        """Archive a conversation."""
        conversation = await self.get_conversation(db, conversation_id, workspace_id)
        if not conversation:
            return False

        conversation.status = ConversationStatus.ARCHIVED
        await db.flush()

        logger.info("Conversation archived", conversation_id=str(conversation_id))
        return True

    async def delete_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
    ) -> bool:
        """Soft delete a conversation."""
        conversation = await self.get_conversation(db, conversation_id, workspace_id)
        if not conversation:
            return False

        conversation.status = ConversationStatus.DELETED
        await db.flush()

        logger.info("Conversation deleted", conversation_id=str(conversation_id))
        return True


# Global service instance
rag_service = RAGService()
