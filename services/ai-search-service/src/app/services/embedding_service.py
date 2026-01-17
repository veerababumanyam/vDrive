"""CLIP embedding service for semantic photo search."""

import io
from typing import Optional
from uuid import UUID

import numpy as np
import structlog
from PIL import Image
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models import PhotoEmbedding

logger = structlog.get_logger()


class CLIPEmbeddingService:
    """
    Generates CLIP ViT-L/14 embeddings for semantic photo search.

    Features:
    - 1536-dimensional image embeddings
    - Text-to-image similarity search via text embeddings
    - Batch processing support
    - pgvector integration for fast similarity queries
    """

    def __init__(self):
        self._model = None
        self._processor = None
        self._initialized = False

    def _load_model(self):
        """Lazy initialization of CLIP model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                # Use sentence-transformers CLIP for unified text/image embeddings
                self._model = SentenceTransformer("clip-ViT-L-14")
                self._initialized = True
                logger.info(
                    "CLIP model loaded",
                    model=settings.CLIP_MODEL,
                    dimension=settings.CLIP_EMBEDDING_DIMENSION,
                )
            except Exception as e:
                logger.error("Failed to load CLIP model", error=str(e))
                raise

    async def generate_image_embedding(
        self,
        image_bytes: bytes,
    ) -> Optional[np.ndarray]:
        """
        Generate CLIP embedding for an image.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.)

        Returns:
            1536-dimensional numpy array or None if failed
        """
        try:
            self._load_model()

            # Load image
            img = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Generate embedding
            embedding = self._model.encode(img, convert_to_numpy=True)

            # Normalize to unit vector for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            logger.debug(
                "Image embedding generated",
                dimension=len(embedding),
            )

            return embedding.astype(np.float32)

        except Exception as e:
            logger.error("Image embedding generation failed", error=str(e))
            return None

    async def generate_text_embedding(
        self,
        text: str,
    ) -> Optional[np.ndarray]:
        """
        Generate CLIP embedding for a text query.

        Used for text-to-image semantic search where the query
        text embedding is compared against image embeddings.

        Args:
            text: Search query text

        Returns:
            1536-dimensional numpy array or None if failed
        """
        try:
            self._load_model()

            # Generate text embedding
            embedding = self._model.encode(text, convert_to_numpy=True)

            # Normalize to unit vector for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            logger.debug(
                "Text embedding generated",
                text_length=len(text),
                dimension=len(embedding),
            )

            return embedding.astype(np.float32)

        except Exception as e:
            logger.error("Text embedding generation failed", error=str(e))
            return None

    async def generate_batch_image_embeddings(
        self,
        images: list[bytes],
    ) -> list[Optional[np.ndarray]]:
        """
        Generate CLIP embeddings for multiple images.

        Args:
            images: List of raw image bytes

        Returns:
            List of embeddings (None for any that failed)
        """
        try:
            self._load_model()

            # Load all images
            pil_images = []
            for img_bytes in images:
                try:
                    img = Image.open(io.BytesIO(img_bytes))
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    pil_images.append(img)
                except Exception as e:
                    logger.warning("Failed to load image in batch", error=str(e))
                    pil_images.append(None)

            # Filter valid images
            valid_images = [img for img in pil_images if img is not None]
            valid_indices = [i for i, img in enumerate(pil_images) if img is not None]

            if not valid_images:
                return [None] * len(images)

            # Batch encode
            embeddings = self._model.encode(
                valid_images,
                batch_size=settings.CLIP_MAX_BATCH_SIZE,
                convert_to_numpy=True,
            )

            # Normalize all embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms > 0, norms, 1)  # Avoid division by zero
            embeddings = embeddings / norms

            # Map back to original indices
            results: list[Optional[np.ndarray]] = [None] * len(images)
            for i, idx in enumerate(valid_indices):
                results[idx] = embeddings[i].astype(np.float32)

            logger.info(
                "Batch image embeddings generated",
                total=len(images),
                successful=len(valid_images),
            )

            return results

        except Exception as e:
            logger.error("Batch embedding generation failed", error=str(e))
            return [None] * len(images)

    async def store_embedding(
        self,
        db: AsyncSession,
        asset_id: UUID,
        workspace_id: UUID,
        embedding: np.ndarray,
        image_description: Optional[str] = None,
    ) -> PhotoEmbedding:
        """
        Store an embedding in the database.

        Args:
            db: Database session
            asset_id: Asset ID
            workspace_id: Workspace ID
            embedding: Embedding vector
            image_description: Optional description

        Returns:
            Created PhotoEmbedding record
        """
        # Convert numpy array to list for pgvector
        embedding_list = embedding.tolist()

        photo_embedding = PhotoEmbedding(
            asset_id=asset_id,
            workspace_id=workspace_id,
            embedding=embedding_list,
            model_name=settings.CLIP_MODEL,
            model_version="1.0",
            image_description=image_description,
        )

        db.add(photo_embedding)
        await db.flush()
        await db.refresh(photo_embedding)

        logger.info(
            "Photo embedding stored",
            asset_id=str(asset_id),
            workspace_id=str(workspace_id),
        )

        return photo_embedding

    async def get_embedding(
        self,
        db: AsyncSession,
        asset_id: UUID,
        workspace_id: UUID,
    ) -> Optional[PhotoEmbedding]:
        """Get existing embedding for an asset."""
        result = await db.execute(
            select(PhotoEmbedding)
            .where(PhotoEmbedding.asset_id == asset_id)
            .where(PhotoEmbedding.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def delete_embedding(
        self,
        db: AsyncSession,
        asset_id: UUID,
        workspace_id: UUID,
    ) -> bool:
        """Delete embedding for an asset."""
        result = await db.execute(
            select(PhotoEmbedding)
            .where(PhotoEmbedding.asset_id == asset_id)
            .where(PhotoEmbedding.workspace_id == workspace_id)
        )
        embedding = result.scalar_one_or_none()

        if embedding:
            await db.delete(embedding)
            logger.info("Photo embedding deleted", asset_id=str(asset_id))
            return True

        return False


# Global service instance
embedding_service = CLIPEmbeddingService()
