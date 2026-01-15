"""Face embedding service using DeepFace/ArcFace for 512-dim vectors."""

from typing import Optional
from uuid import UUID
import io
import numpy as np

import structlog
from PIL import Image
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.circuit_breaker import circuit_breaker
from ..models import Face, FaceEmbedding

logger = structlog.get_logger()


class EmbeddingService:
    """
    Generates face embeddings using DeepFace with ArcFace model.

    Features:
    - 512-dimensional embeddings for face recognition
    - Face alignment before embedding
    - pgvector similarity search
    """

    def __init__(self):
        self._model = None
        self._initialized = False

    def _get_model(self):
        """Lazy initialization of DeepFace model."""
        if self._model is None:
            try:
                from deepface import DeepFace

                # Pre-load the model
                DeepFace.build_model("ArcFace")
                self._model = DeepFace
                self._initialized = True
                logger.info("DeepFace ArcFace model loaded")
            except Exception as e:
                logger.error("Failed to load DeepFace model", error=str(e))
                raise
        return self._model

    @circuit_breaker("deepface")
    async def generate_embedding(
        self,
        image_bytes: bytes,
        bounding_box: Optional[dict[str, float]] = None,
    ) -> Optional[np.ndarray]:
        """
        Generate a 512-dim face embedding from an image.

        Args:
            image_bytes: Raw image bytes
            bounding_box: Optional normalized bounding box to crop

        Returns:
            512-dimensional numpy array or None if failed
        """
        try:
            model = self._get_model()

            # Load image
            img = Image.open(io.BytesIO(image_bytes))

            # Crop to bounding box if provided
            if bounding_box:
                img = self._crop_to_bbox(img, bounding_box)

            # Convert to numpy array
            img_array = np.array(img)

            # Generate embedding using ArcFace
            # DeepFace handles face alignment internally
            result = model.represent(
                img_array,
                model_name="ArcFace",
                enforce_detection=False,  # We already detected the face
                detector_backend="skip",  # Skip detection since we have bbox
            )

            if result and len(result) > 0:
                embedding = np.array(result[0]["embedding"], dtype=np.float32)

                # Normalize to unit vector for cosine similarity
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm

                logger.debug(
                    "Face embedding generated",
                    dimension=len(embedding),
                )

                return embedding

            return None

        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            return None

    def _crop_to_bbox(
        self,
        img: Image.Image,
        bbox: dict[str, float],
    ) -> Image.Image:
        """Crop image to bounding box with padding."""
        width, height = img.size

        # Convert normalized coordinates to pixels
        x = int(bbox["x"] * width)
        y = int(bbox["y"] * height)
        w = int(bbox["width"] * width)
        h = int(bbox["height"] * height)

        # Add 20% padding for better embedding
        pad_x = int(w * 0.2)
        pad_y = int(h * 0.2)

        left = max(0, x - pad_x)
        top = max(0, y - pad_y)
        right = min(width, x + w + pad_x)
        bottom = min(height, y + h + pad_y)

        return img.crop((left, top, right, bottom))

    async def find_similar_faces(
        self,
        db: AsyncSession,
        embedding: np.ndarray,
        workspace_id: UUID,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list[dict]:
        """
        Find similar faces using pgvector cosine similarity.

        Args:
            db: Database session
            embedding: Query embedding vector
            workspace_id: Workspace to search in
            limit: Maximum results to return
            threshold: Minimum similarity threshold (0-1)

        Returns:
            List of similar faces with similarity scores
        """
        try:
            # Convert embedding to pgvector format
            embedding_str = "[" + ",".join(str(x) for x in embedding.tolist()) + "]"

            # Use pgvector's <=> operator for cosine distance
            # Note: <=> returns distance, so we convert to similarity
            query = text(
                """
                SELECT
                    fe.id,
                    fe.face_id,
                    f.asset_id,
                    f.group_id,
                    f.bounding_box,
                    1 - (fe.embedding <=> :embedding::vector) as similarity
                FROM face_embeddings fe
                JOIN faces f ON f.id = fe.face_id
                WHERE f.workspace_id = :workspace_id
                AND 1 - (fe.embedding <=> :embedding::vector) >= :threshold
                ORDER BY fe.embedding <=> :embedding::vector
                LIMIT :limit
                """
            )

            result = await db.execute(
                query,
                {
                    "embedding": embedding_str,
                    "workspace_id": str(workspace_id),
                    "threshold": threshold,
                    "limit": limit,
                },
            )

            rows = result.fetchall()

            return [
                {
                    "embedding_id": str(row.id),
                    "face_id": str(row.face_id),
                    "asset_id": str(row.asset_id),
                    "group_id": str(row.group_id) if row.group_id else None,
                    "bounding_box": row.bounding_box,
                    "similarity": float(row.similarity),
                }
                for row in rows
            ]

        except Exception as e:
            logger.error("Similarity search failed", error=str(e))
            return []

    async def find_face_matches_for_selfie(
        self,
        db: AsyncSession,
        selfie_embedding: np.ndarray,
        workspace_id: UUID,
        limit: int = 50,
        threshold: float = 0.6,
    ) -> list[dict]:
        """
        Find matching faces for a selfie (Find Me feature).

        Args:
            db: Database session
            selfie_embedding: Embedding from uploaded selfie
            workspace_id: Workspace to search
            limit: Maximum matches to return
            threshold: Similarity threshold (lower for selfie matching)

        Returns:
            List of matching assets with face info
        """
        return await self.find_similar_faces(
            db=db,
            embedding=selfie_embedding,
            workspace_id=workspace_id,
            limit=limit,
            threshold=threshold,
        )


# Global service instance
embedding_service = EmbeddingService()
