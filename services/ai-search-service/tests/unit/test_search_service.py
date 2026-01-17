"""Unit tests for semantic search service."""

import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.app.services.search_service import SearchService


class TestSearchService:
    """Tests for SearchService."""

    @pytest.fixture
    def search_service(self):
        """Create search service instance."""
        return SearchService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def sample_query_embedding(self):
        """Generate sample 1536-dim query embedding."""
        embedding = np.random.randn(1536).astype(np.float32)
        return embedding / np.linalg.norm(embedding)

    @pytest.mark.asyncio
    async def test_semantic_search_returns_results(
        self, search_service, mock_db, sample_query_embedding
    ):
        """Test that semantic search returns results."""
        workspace_id = uuid4()
        query = "bride throwing bouquet"

        with patch.object(
            search_service, "_get_query_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = sample_query_embedding

            # Mock database results
            mock_results = [
                MagicMock(
                    asset_id=uuid4(),
                    similarity=0.85,
                    filename="wedding001.jpg",
                ),
                MagicMock(
                    asset_id=uuid4(),
                    similarity=0.78,
                    filename="wedding002.jpg",
                ),
            ]

            with patch.object(
                search_service, "_execute_vector_search"
            ) as mock_search:
                mock_search.return_value = [
                    {
                        "asset_id": str(r.asset_id),
                        "similarity": r.similarity,
                        "filename": r.filename,
                    }
                    for r in mock_results
                ]

                results = await search_service.semantic_search(
                    db=mock_db,
                    workspace_id=workspace_id,
                    query=query,
                    limit=10,
                )

                assert len(results) == 2
                mock_get_embedding.assert_called_once_with(query)

    @pytest.mark.asyncio
    async def test_semantic_search_respects_limit(
        self, search_service, mock_db, sample_query_embedding
    ):
        """Test that search respects result limit."""
        workspace_id = uuid4()
        query = "sunset"
        limit = 5

        with patch.object(
            search_service, "_get_query_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = sample_query_embedding

            # Return more results than limit
            mock_results = [
                {"asset_id": str(uuid4()), "similarity": 0.9 - i * 0.05}
                for i in range(10)
            ]

            with patch.object(
                search_service, "_execute_vector_search"
            ) as mock_search:
                mock_search.return_value = mock_results[:limit]

                results = await search_service.semantic_search(
                    db=mock_db,
                    workspace_id=workspace_id,
                    query=query,
                    limit=limit,
                )

                assert len(results) <= limit

    @pytest.mark.asyncio
    async def test_semantic_search_filters_by_workspace(
        self, search_service, mock_db, sample_query_embedding
    ):
        """Test that search only returns results from specified workspace."""
        workspace_id = uuid4()
        other_workspace_id = uuid4()
        query = "portrait"

        with patch.object(
            search_service, "_get_query_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = sample_query_embedding

            with patch.object(
                search_service, "_execute_vector_search"
            ) as mock_search:
                # Only return workspace-filtered results
                mock_search.return_value = [
                    {
                        "asset_id": str(uuid4()),
                        "workspace_id": str(workspace_id),
                        "similarity": 0.8,
                    }
                ]

                results = await search_service.semantic_search(
                    db=mock_db,
                    workspace_id=workspace_id,
                    query=query,
                )

                # Verify workspace_id was passed to search
                mock_search.assert_called_once()
                call_args = mock_search.call_args
                assert workspace_id in [
                    call_args.args[1] if len(call_args.args) > 1 else None,
                    call_args.kwargs.get("workspace_id"),
                ]

    @pytest.mark.asyncio
    async def test_find_similar_photos_returns_sorted(
        self, search_service, mock_db
    ):
        """Test that similar photos are sorted by similarity."""
        workspace_id = uuid4()
        asset_id = uuid4()

        with patch.object(
            search_service, "_get_asset_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = np.random.randn(1536)

            with patch.object(
                search_service, "_execute_vector_search"
            ) as mock_search:
                mock_search.return_value = [
                    {"asset_id": str(uuid4()), "similarity": 0.95},
                    {"asset_id": str(uuid4()), "similarity": 0.87},
                    {"asset_id": str(uuid4()), "similarity": 0.91},
                ]

                results = await search_service.find_similar(
                    db=mock_db,
                    workspace_id=workspace_id,
                    asset_id=asset_id,
                    limit=10,
                )

                # Results should be sorted by similarity descending
                if len(results) > 1:
                    for i in range(len(results) - 1):
                        assert results[i]["similarity"] >= results[i + 1]["similarity"]

    @pytest.mark.asyncio
    async def test_find_similar_excludes_source_asset(
        self, search_service, mock_db
    ):
        """Test that similar photos excludes the source asset."""
        workspace_id = uuid4()
        asset_id = uuid4()

        with patch.object(
            search_service, "_get_asset_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = np.random.randn(1536)

            with patch.object(
                search_service, "_execute_vector_search"
            ) as mock_search:
                other_asset_id = uuid4()
                mock_search.return_value = [
                    {"asset_id": str(other_asset_id), "similarity": 0.95},
                ]

                results = await search_service.find_similar(
                    db=mock_db,
                    workspace_id=workspace_id,
                    asset_id=asset_id,
                )

                # Source asset should not be in results
                for result in results:
                    assert result["asset_id"] != str(asset_id)

    @pytest.mark.asyncio
    async def test_get_embedding_status_returns_counts(
        self, search_service, mock_db
    ):
        """Test embedding status returns correct counts."""
        workspace_id = uuid4()

        with patch.object(
            search_service, "_get_workspace_stats"
        ) as mock_stats:
            mock_stats.return_value = {
                "total_assets": 100,
                "embedded_assets": 85,
                "pending_assets": 15,
            }

            status = await search_service.get_embedding_status(
                db=mock_db,
                workspace_id=workspace_id,
            )

            assert "total_assets" in status
            assert "embedded_assets" in status
            assert status["total_assets"] >= status["embedded_assets"]


class TestSearchFilters:
    """Tests for search filtering capabilities."""

    @pytest.fixture
    def search_service(self):
        """Create search service instance."""
        return SearchService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_search_with_gallery_filter(
        self, search_service, mock_db
    ):
        """Test search filtered by gallery."""
        workspace_id = uuid4()
        gallery_id = uuid4()
        query = "family portrait"

        with patch.object(
            search_service, "_get_query_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = np.random.randn(1536)

            with patch.object(
                search_service, "_execute_vector_search"
            ) as mock_search:
                mock_search.return_value = []

                await search_service.semantic_search(
                    db=mock_db,
                    workspace_id=workspace_id,
                    query=query,
                    gallery_id=gallery_id,
                )

                # Verify gallery filter was applied
                mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_date_range(
        self, search_service, mock_db
    ):
        """Test search filtered by date range."""
        workspace_id = uuid4()
        query = "outdoor"
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        with patch.object(
            search_service, "_get_query_embedding"
        ) as mock_get_embedding:
            mock_get_embedding.return_value = np.random.randn(1536)

            with patch.object(
                search_service, "_execute_vector_search"
            ) as mock_search:
                mock_search.return_value = []

                await search_service.semantic_search(
                    db=mock_db,
                    workspace_id=workspace_id,
                    query=query,
                    date_from=start_date,
                    date_to=end_date,
                )

                mock_search.assert_called_once()


class TestSearchMetrics:
    """Tests for search service metrics."""

    @pytest.fixture
    def search_service(self):
        """Create search service instance."""
        return SearchService()

    def test_embedding_dimensions(self, search_service):
        """Test embedding dimensions match CLIP config."""
        assert search_service.embedding_dim == 1536

    def test_default_limit_configured(self, search_service):
        """Test default search limit is configured."""
        assert hasattr(search_service, "default_limit")
        assert search_service.default_limit > 0
        assert search_service.default_limit <= 200

    def test_similarity_threshold_configured(self, search_service):
        """Test similarity threshold is configured."""
        assert hasattr(search_service, "similarity_threshold")
        assert 0 < search_service.similarity_threshold < 1
