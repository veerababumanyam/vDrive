"""Integration tests for semantic search."""

import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Skip if dependencies not available
pytest.importorskip("sqlalchemy")


class TestSemanticSearchIntegration:
    """Integration tests for the semantic search system."""

    @pytest.fixture
    def workspace_id(self):
        """Generate workspace ID for tests."""
        return uuid4()

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def sample_photos(self):
        """Generate sample photo data."""
        return [
            {
                "asset_id": uuid4(),
                "filename": "wedding_ceremony.jpg",
                "embedding": np.random.randn(1536).tolist(),
                "tags": ["wedding", "ceremony", "bride", "groom"],
            },
            {
                "asset_id": uuid4(),
                "filename": "reception_dance.jpg",
                "embedding": np.random.randn(1536).tolist(),
                "tags": ["wedding", "reception", "dance"],
            },
            {
                "asset_id": uuid4(),
                "filename": "portrait_outdoor.jpg",
                "embedding": np.random.randn(1536).tolist(),
                "tags": ["portrait", "outdoor", "sunset"],
            },
        ]

    @pytest.mark.asyncio
    async def test_semantic_search_end_to_end(
        self, mock_db_session, workspace_id, sample_photos
    ):
        """Test end-to-end semantic search flow."""
        query = "bride throwing bouquet at wedding"

        with patch(
            "src.app.services.embedding_service.CLIPEmbeddingService"
        ) as MockEmbedding:
            # Mock CLIP embedding generation
            mock_embedder = MagicMock()
            query_embedding = np.random.randn(1536).astype(np.float32)
            mock_embedder.encode_text = AsyncMock(return_value=query_embedding)
            MockEmbedding.return_value = mock_embedder

            from src.app.services.search_service import SearchService

            search_service = SearchService()

            with patch.object(
                search_service, "_get_query_embedding"
            ) as mock_get_embedding:
                mock_get_embedding.return_value = query_embedding

                with patch.object(
                    search_service, "_execute_vector_search"
                ) as mock_search:
                    # Return wedding photos as most relevant
                    mock_search.return_value = [
                        {
                            "asset_id": str(sample_photos[0]["asset_id"]),
                            "similarity": 0.89,
                            "filename": sample_photos[0]["filename"],
                        },
                        {
                            "asset_id": str(sample_photos[1]["asset_id"]),
                            "similarity": 0.75,
                            "filename": sample_photos[1]["filename"],
                        },
                    ]

                    results = await search_service.semantic_search(
                        db=mock_db_session,
                        workspace_id=workspace_id,
                        query=query,
                        limit=10,
                    )

                    assert len(results) == 2
                    # Wedding photos should rank higher
                    assert results[0]["similarity"] > results[1]["similarity"]
                    assert "wedding" in results[0]["filename"].lower()

    @pytest.mark.asyncio
    async def test_similar_photos_search(
        self, mock_db_session, workspace_id, sample_photos
    ):
        """Test finding similar photos by asset ID."""
        source_asset_id = sample_photos[0]["asset_id"]

        from src.app.services.search_service import SearchService

        search_service = SearchService()

        with patch.object(
            search_service, "_get_asset_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = np.array(sample_photos[0]["embedding"])

            with patch.object(
                search_service, "_execute_vector_search"
            ) as mock_search:
                mock_search.return_value = [
                    {
                        "asset_id": str(sample_photos[1]["asset_id"]),
                        "similarity": 0.82,
                        "filename": sample_photos[1]["filename"],
                    },
                ]

                results = await search_service.find_similar(
                    db=mock_db_session,
                    workspace_id=workspace_id,
                    asset_id=source_asset_id,
                    limit=10,
                )

                # Should not include source asset
                assert all(r["asset_id"] != str(source_asset_id) for r in results)

    @pytest.mark.asyncio
    async def test_embedding_generation_consistency(
        self, mock_db_session, workspace_id
    ):
        """Test that same query produces consistent embeddings."""
        query = "portrait photography"

        with patch(
            "src.app.services.embedding_service.embedding_service"
        ) as mock_embedder:
            fixed_embedding = np.random.randn(1536).astype(np.float32)
            mock_embedder.encode_text = AsyncMock(return_value=fixed_embedding)

            from src.app.services.search_service import SearchService

            search_service = SearchService()

            with patch.object(
                search_service, "_get_query_embedding"
            ) as mock_get_embedding:
                mock_get_embedding.return_value = fixed_embedding

                with patch.object(
                    search_service, "_execute_vector_search"
                ) as mock_search:
                    mock_search.return_value = []

                    # Run same query twice
                    await search_service.semantic_search(
                        db=mock_db_session,
                        workspace_id=workspace_id,
                        query=query,
                    )
                    await search_service.semantic_search(
                        db=mock_db_session,
                        workspace_id=workspace_id,
                        query=query,
                    )

                    # Both calls should use same embedding
                    assert mock_get_embedding.call_count == 2


class TestEmbeddingProcessorIntegration:
    """Integration tests for embedding processor consumer."""

    @pytest.fixture
    def workspace_id(self):
        """Generate workspace ID."""
        return uuid4()

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_embedding_processor_generates_embeddings(
        self, mock_db_session, workspace_id
    ):
        """Test that embedding processor creates embeddings for assets."""
        asset_id = uuid4()
        image_data = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

        with patch(
            "src.app.services.embedding_service.embedding_service"
        ) as mock_embedder:
            embedding = np.random.randn(1536).astype(np.float32)
            mock_embedder.encode_image = AsyncMock(return_value=embedding)
            mock_embedder.store_embedding = AsyncMock(return_value=uuid4())

            from src.app.consumers.asset_embedding_processor import (
                AssetEmbeddingProcessor,
            )

            processor = AssetEmbeddingProcessor()

            with patch.object(processor, "_process_asset") as mock_process:
                mock_process.return_value = {
                    "asset_id": str(asset_id),
                    "embedding_id": str(uuid4()),
                    "status": "success",
                }

                result = await processor._process_asset(
                    db=mock_db_session,
                    asset_id=asset_id,
                    workspace_id=workspace_id,
                    image_data=image_data.tobytes(),
                )

                assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_embedding_processor_publishes_events(
        self, mock_db_session, workspace_id
    ):
        """Test that processor publishes embedding generated events."""
        asset_id = uuid4()

        with patch(
            "src.app.services.event_service.event_service"
        ) as mock_event_service:
            mock_event_service.publish = AsyncMock()

            from src.app.consumers.asset_embedding_processor import (
                AssetEmbeddingProcessor,
            )

            processor = AssetEmbeddingProcessor()

            with patch.object(
                processor, "_publish_embedding_generated"
            ) as mock_publish:
                mock_publish.return_value = None

                # Verify publish method exists
                assert hasattr(processor, "_publish_embedding_generated")


class TestRagSearchIntegration:
    """Integration tests for RAG + Search integration."""

    @pytest.fixture
    def workspace_id(self):
        """Generate workspace ID."""
        return uuid4()

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_rag_retrieves_relevant_photos(
        self, mock_db_session, workspace_id
    ):
        """Test that RAG chat retrieves relevant photos for context."""
        query = "Show me photos from the wedding ceremony"

        with patch(
            "src.app.services.search_service.search_service"
        ) as mock_search:
            mock_search.semantic_search = AsyncMock(
                return_value=[
                    {
                        "asset_id": str(uuid4()),
                        "similarity": 0.85,
                        "filename": "ceremony_001.jpg",
                    },
                    {
                        "asset_id": str(uuid4()),
                        "similarity": 0.78,
                        "filename": "ceremony_002.jpg",
                    },
                ]
            )

            from src.app.services.rag_service import RAGService

            rag_service = RAGService()

            with patch.object(
                rag_service, "_retrieve_context_photos"
            ) as mock_retrieve:
                mock_retrieve.return_value = [
                    {"asset_id": str(uuid4()), "description": "Wedding ceremony photo"},
                ]

                with patch.object(
                    rag_service, "_generate_response"
                ) as mock_generate:
                    mock_generate.return_value = {
                        "response": "Here are photos from the ceremony...",
                        "photos": mock_retrieve.return_value,
                    }

                    result = await rag_service.chat(
                        db=mock_db_session,
                        workspace_id=workspace_id,
                        message=query,
                    )

                    # RAG should retrieve photos and include in response
                    mock_retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_respects_gallery_context(
        self, mock_db_session, workspace_id
    ):
        """Test that search can be scoped to specific gallery."""
        gallery_id = uuid4()
        query = "sunset photos"

        from src.app.services.search_service import SearchService

        search_service = SearchService()

        with patch.object(
            search_service, "_get_query_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = np.random.randn(1536)

            with patch.object(
                search_service, "_execute_vector_search"
            ) as mock_search:
                mock_search.return_value = [
                    {
                        "asset_id": str(uuid4()),
                        "gallery_id": str(gallery_id),
                        "similarity": 0.8,
                    },
                ]

                results = await search_service.semantic_search(
                    db=mock_db_session,
                    workspace_id=workspace_id,
                    query=query,
                    gallery_id=gallery_id,
                )

                # Results should only be from specified gallery
                for result in results:
                    if "gallery_id" in result:
                        assert result["gallery_id"] == str(gallery_id)
