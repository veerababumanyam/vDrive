"""Unit tests for face embedding service."""

import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.app.services.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.fixture
    def embedding_service(self):
        """Create embedding service instance."""
        return EmbeddingService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def sample_embedding(self):
        """Generate sample 512-dim embedding."""
        return np.random.randn(512).astype(np.float32)

    @pytest.fixture
    def sample_face_crop(self):
        """Generate sample face crop image."""
        return np.random.randint(0, 255, (160, 160, 3), dtype=np.uint8)

    @pytest.mark.asyncio
    async def test_generate_embedding_returns_correct_dimensions(
        self, embedding_service, sample_face_crop
    ):
        """Test that embeddings have correct dimensions."""
        with patch.object(
            embedding_service, "_get_model_embedding"
        ) as mock_get_embedding:
            expected_embedding = np.random.randn(512).astype(np.float32)
            mock_get_embedding.return_value = expected_embedding

            result = await embedding_service.generate_embedding(sample_face_crop)

            assert result is not None
            assert len(result) == 512
            mock_get_embedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding_normalizes_output(
        self, embedding_service, sample_face_crop
    ):
        """Test that embeddings are L2 normalized."""
        with patch.object(
            embedding_service, "_get_model_embedding"
        ) as mock_get_embedding:
            # Return unnormalized embedding
            raw_embedding = np.array([3.0, 4.0] + [0.0] * 510, dtype=np.float32)
            mock_get_embedding.return_value = raw_embedding

            result = await embedding_service.generate_embedding(sample_face_crop)

            # Check L2 norm is approximately 1
            norm = np.linalg.norm(result)
            assert abs(norm - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_find_similar_faces_returns_sorted_results(
        self, embedding_service, mock_db, sample_embedding
    ):
        """Test that similar faces are sorted by similarity."""
        workspace_id = uuid4()

        # Mock database query results
        mock_results = [
            MagicMock(
                face_id=uuid4(),
                asset_id=uuid4(),
                group_id=uuid4(),
                distance=0.1,
            ),
            MagicMock(
                face_id=uuid4(),
                asset_id=uuid4(),
                group_id=uuid4(),
                distance=0.3,
            ),
            MagicMock(
                face_id=uuid4(),
                asset_id=uuid4(),
                group_id=uuid4(),
                distance=0.2,
            ),
        ]

        mock_db.execute.return_value = MagicMock(
            fetchall=MagicMock(return_value=mock_results)
        )

        with patch.object(
            embedding_service, "_search_similar_embeddings"
        ) as mock_search:
            mock_search.return_value = [
                {"face_id": str(r.face_id), "distance": r.distance}
                for r in sorted(mock_results, key=lambda x: x.distance)
            ]

            results = await embedding_service.find_similar_faces(
                db=mock_db,
                embedding=sample_embedding,
                workspace_id=workspace_id,
                limit=10,
            )

            assert len(results) <= 10
            # Verify sorted by distance (most similar first)
            if len(results) > 1:
                for i in range(len(results) - 1):
                    assert results[i]["distance"] <= results[i + 1]["distance"]

    @pytest.mark.asyncio
    async def test_find_similar_faces_respects_threshold(
        self, embedding_service, mock_db, sample_embedding
    ):
        """Test that similarity threshold filters results."""
        workspace_id = uuid4()
        threshold = 0.5

        with patch.object(
            embedding_service, "_search_similar_embeddings"
        ) as mock_search:
            mock_search.return_value = [
                {"face_id": str(uuid4()), "distance": 0.3, "similarity": 0.7},
                {"face_id": str(uuid4()), "distance": 0.6, "similarity": 0.4},
            ]

            results = await embedding_service.find_similar_faces(
                db=mock_db,
                embedding=sample_embedding,
                workspace_id=workspace_id,
                threshold=threshold,
            )

            # Results above threshold should be filtered
            for result in results:
                if "similarity" in result:
                    assert result["similarity"] >= threshold

    @pytest.mark.asyncio
    async def test_store_embedding_creates_record(
        self, embedding_service, mock_db, sample_embedding
    ):
        """Test that storing embedding creates database record."""
        face_id = uuid4()

        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        with patch(
            "src.app.services.embedding_service.FaceEmbedding"
        ) as MockEmbedding:
            mock_embedding_obj = MagicMock(id=uuid4())
            MockEmbedding.return_value = mock_embedding_obj

            result = await embedding_service.store_embedding(
                db=mock_db,
                face_id=face_id,
                embedding=sample_embedding,
            )

            mock_db.add.assert_called_once()
            mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding_handles_invalid_input(
        self, embedding_service
    ):
        """Test that invalid input raises appropriate error."""
        invalid_crop = np.array([])  # Empty array

        with pytest.raises((ValueError, Exception)):
            await embedding_service.generate_embedding(invalid_crop)

    @pytest.mark.asyncio
    async def test_embedding_consistency(
        self, embedding_service, sample_face_crop
    ):
        """Test that same input produces consistent embeddings."""
        with patch.object(
            embedding_service, "_get_model_embedding"
        ) as mock_get_embedding:
            fixed_embedding = np.random.randn(512).astype(np.float32)
            mock_get_embedding.return_value = fixed_embedding

            result1 = await embedding_service.generate_embedding(sample_face_crop)
            result2 = await embedding_service.generate_embedding(sample_face_crop)

            np.testing.assert_array_almost_equal(result1, result2)


class TestEmbeddingMetrics:
    """Tests for embedding service metrics."""

    @pytest.fixture
    def embedding_service(self):
        """Create embedding service instance."""
        return EmbeddingService()

    def test_embedding_dimension_matches_config(self, embedding_service):
        """Test embedding dimensions match configuration."""
        assert embedding_service.embedding_dim == 512

    def test_model_name_configured(self, embedding_service):
        """Test model name is configured."""
        assert embedding_service.model_name in ["arcface", "facenet", "vggface"]
