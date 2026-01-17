"""Semantic search service using pgvector similarity search."""

from typing import Optional
from uuid import UUID

import numpy as np
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from .embedding_service import embedding_service

logger = structlog.get_logger()


class SearchService:
    """
    Semantic search service for natural language photo queries.

    Features:
    - Text-to-image search using CLIP embeddings
    - Similar photo discovery
    - Workspace-scoped queries
    - Configurable similarity thresholds
    """

    async def semantic_search(
        self,
        db: AsyncSession,
        query: str,
        workspace_id: UUID,
        limit: int = 50,
        threshold: float = 0.0,
        offset: int = 0,
    ) -> list[dict]:
        """
        Search photos using natural language query.

        Converts text query to CLIP embedding and finds
        semantically similar images using pgvector cosine similarity.

        Args:
            db: Database session
            query: Natural language search query
            workspace_id: Workspace to search in
            limit: Maximum results to return
            threshold: Minimum similarity score (0-1)
            offset: Pagination offset

        Returns:
            List of matching photos with similarity scores
        """
        try:
            # Generate text embedding for query
            query_embedding = await embedding_service.generate_text_embedding(query)

            if query_embedding is None:
                logger.error("Failed to generate query embedding", query=query)
                return []

            return await self._vector_search(
                db=db,
                embedding=query_embedding,
                workspace_id=workspace_id,
                limit=limit,
                threshold=threshold,
                offset=offset,
            )

        except Exception as e:
            logger.error("Semantic search failed", query=query, error=str(e))
            return []

    async def find_similar_photos(
        self,
        db: AsyncSession,
        asset_id: UUID,
        workspace_id: UUID,
        limit: int = 20,
        threshold: float = 0.5,
    ) -> list[dict]:
        """
        Find photos similar to a given photo.

        Uses the existing photo embedding to find visually similar images.

        Args:
            db: Database session
            asset_id: Source asset ID
            workspace_id: Workspace to search in
            limit: Maximum results to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of similar photos with similarity scores
        """
        try:
            # Get existing embedding for the source photo
            photo_embedding = await embedding_service.get_embedding(
                db=db,
                asset_id=asset_id,
                workspace_id=workspace_id,
            )

            if not photo_embedding:
                logger.warning(
                    "No embedding found for asset",
                    asset_id=str(asset_id),
                )
                return []

            # Convert stored embedding to numpy array
            embedding = np.array(photo_embedding.embedding, dtype=np.float32)

            # Search for similar photos (excluding the source)
            results = await self._vector_search(
                db=db,
                embedding=embedding,
                workspace_id=workspace_id,
                limit=limit + 1,  # Get one extra to filter out source
                threshold=threshold,
                offset=0,
                exclude_asset_id=asset_id,
            )

            # Filter out the source photo if it appears
            results = [r for r in results if UUID(r["asset_id"]) != asset_id][:limit]

            return results

        except Exception as e:
            logger.error(
                "Find similar photos failed",
                asset_id=str(asset_id),
                error=str(e),
            )
            return []

    async def _vector_search(
        self,
        db: AsyncSession,
        embedding: np.ndarray,
        workspace_id: UUID,
        limit: int,
        threshold: float,
        offset: int = 0,
        exclude_asset_id: Optional[UUID] = None,
    ) -> list[dict]:
        """
        Execute pgvector similarity search.

        Args:
            db: Database session
            embedding: Query embedding vector
            workspace_id: Workspace to search in
            limit: Maximum results
            threshold: Minimum similarity score
            offset: Pagination offset
            exclude_asset_id: Optional asset ID to exclude

        Returns:
            List of matching assets with similarity scores
        """
        try:
            # Convert embedding to pgvector format
            embedding_str = "[" + ",".join(str(x) for x in embedding.tolist()) + "]"

            # Build query with optional exclusion
            exclude_clause = ""
            params = {
                "embedding": embedding_str,
                "workspace_id": str(workspace_id),
                "threshold": threshold,
                "limit": limit,
                "offset": offset,
            }

            if exclude_asset_id:
                exclude_clause = "AND pe.asset_id != :exclude_asset_id"
                params["exclude_asset_id"] = str(exclude_asset_id)

            # Use pgvector's <=> operator for cosine distance
            # 1 - distance = similarity
            query = text(
                f"""
                SELECT
                    pe.id,
                    pe.asset_id,
                    pe.workspace_id,
                    pe.model_name,
                    pe.image_description,
                    pe.created_at,
                    1 - (pe.embedding <=> :embedding::vector) as similarity
                FROM photo_embeddings pe
                WHERE pe.workspace_id = :workspace_id
                AND 1 - (pe.embedding <=> :embedding::vector) >= :threshold
                {exclude_clause}
                ORDER BY pe.embedding <=> :embedding::vector
                OFFSET :offset
                LIMIT :limit
                """
            )

            result = await db.execute(query, params)
            rows = result.fetchall()

            return [
                {
                    "id": str(row.id),
                    "asset_id": str(row.asset_id),
                    "workspace_id": str(row.workspace_id),
                    "model_name": row.model_name,
                    "image_description": row.image_description,
                    "similarity": float(row.similarity),
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]

        except Exception as e:
            logger.error("Vector search failed", error=str(e))
            return []

    async def get_search_stats(
        self,
        db: AsyncSession,
        workspace_id: UUID,
    ) -> dict:
        """
        Get search index statistics for a workspace.

        Args:
            db: Database session
            workspace_id: Workspace ID

        Returns:
            Dictionary with statistics
        """
        try:
            query = text(
                """
                SELECT
                    COUNT(*) as total_embeddings,
                    MIN(created_at) as oldest_embedding,
                    MAX(created_at) as newest_embedding
                FROM photo_embeddings
                WHERE workspace_id = :workspace_id
                """
            )

            result = await db.execute(query, {"workspace_id": str(workspace_id)})
            row = result.fetchone()

            return {
                "total_embeddings": row.total_embeddings if row else 0,
                "oldest_embedding": (
                    row.oldest_embedding.isoformat() if row and row.oldest_embedding else None
                ),
                "newest_embedding": (
                    row.newest_embedding.isoformat() if row and row.newest_embedding else None
                ),
            }

        except Exception as e:
            logger.error("Failed to get search stats", error=str(e))
            return {
                "total_embeddings": 0,
                "oldest_embedding": None,
                "newest_embedding": None,
            }


# Global service instance
search_service = SearchService()
