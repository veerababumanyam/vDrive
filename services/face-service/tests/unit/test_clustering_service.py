"""Unit tests for face clustering service."""

import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.app.services.clustering_service import ClusteringService


class TestClusteringService:
    """Tests for ClusteringService."""

    @pytest.fixture
    def clustering_service(self):
        """Create clustering service instance."""
        return ClusteringService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.fixture
    def sample_embeddings(self):
        """Generate sample embeddings for clustering."""
        # Create 3 clusters of faces
        cluster1 = np.random.randn(5, 512).astype(np.float32) * 0.1
        cluster2 = np.random.randn(5, 512).astype(np.float32) * 0.1 + 2
        cluster3 = np.random.randn(5, 512).astype(np.float32) * 0.1 + 4
        return np.vstack([cluster1, cluster2, cluster3])

    @pytest.mark.asyncio
    async def test_cluster_faces_creates_groups(
        self, clustering_service, mock_db, sample_embeddings
    ):
        """Test that clustering creates appropriate face groups."""
        workspace_id = uuid4()

        # Mock face and embedding data
        mock_faces = []
        for i, emb in enumerate(sample_embeddings):
            mock_face = MagicMock(
                id=uuid4(),
                workspace_id=workspace_id,
                group_id=None,
            )
            mock_embedding = MagicMock(embedding=emb.tolist())
            mock_faces.append((mock_face, mock_embedding))

        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_faces
        mock_db.execute.return_value = mock_result

        with patch("src.app.services.clustering_service.FaceGroup") as MockGroup:
            MockGroup.return_value = MagicMock(id=uuid4())

            result = await clustering_service.cluster_faces(
                db=mock_db,
                workspace_id=workspace_id,
            )

            assert "clustered" in result
            assert "groups_created" in result
            assert result["clustered"] == len(sample_embeddings)

    @pytest.mark.asyncio
    async def test_cluster_faces_handles_empty_workspace(
        self, clustering_service, mock_db
    ):
        """Test clustering with no faces returns appropriate result."""
        workspace_id = uuid4()

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        result = await clustering_service.cluster_faces(
            db=mock_db,
            workspace_id=workspace_id,
        )

        assert result["clustered"] == 0
        assert result["groups_created"] == 0

    @pytest.mark.asyncio
    async def test_merge_groups_moves_faces(
        self, clustering_service, mock_db
    ):
        """Test that merging groups moves all faces to target."""
        workspace_id = uuid4()
        source_ids = [uuid4(), uuid4()]
        target_id = uuid4()

        # Mock groups exist
        mock_groups_result = MagicMock()
        mock_groups_result.scalars.return_value = [
            MagicMock(id=source_ids[0]),
            MagicMock(id=source_ids[1]),
            MagicMock(id=target_id),
        ]

        # Mock face count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10

        mock_db.execute.side_effect = [
            mock_groups_result,
            MagicMock(rowcount=3),  # First source group faces moved
            MagicMock(),  # Delete first source group
            MagicMock(rowcount=4),  # Second source group faces moved
            MagicMock(),  # Delete second source group
            mock_count_result,  # Count in target
            MagicMock(),  # Update target count
        ]

        result = await clustering_service.merge_groups(
            db=mock_db,
            source_group_ids=source_ids,
            target_group_id=target_id,
            workspace_id=workspace_id,
        )

        assert "merged" in result
        assert "faces_moved" in result
        assert result["target_group_id"] == str(target_id)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_merge_groups_validates_target_exists(
        self, clustering_service, mock_db
    ):
        """Test that merge fails if target group doesn't exist."""
        workspace_id = uuid4()
        source_ids = [uuid4()]
        target_id = uuid4()

        # Mock no groups found
        mock_result = MagicMock()
        mock_result.scalars.return_value = []
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Target group not found"):
            await clustering_service.merge_groups(
                db=mock_db,
                source_group_ids=source_ids,
                target_group_id=target_id,
                workspace_id=workspace_id,
            )

    @pytest.mark.asyncio
    async def test_split_group_creates_new_group(
        self, clustering_service, mock_db
    ):
        """Test that splitting creates a new group with selected faces."""
        workspace_id = uuid4()
        original_group_id = uuid4()
        face_ids = [uuid4(), uuid4(), uuid4()]

        # Mock original group exists
        mock_group = MagicMock(
            id=original_group_id,
            workspace_id=workspace_id,
            face_count="10",
        )
        mock_group_result = MagicMock()
        mock_group_result.scalar_one_or_none.return_value = mock_group
        mock_db.execute.return_value = mock_group_result

        # Mock remaining count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 7

        with patch("src.app.services.clustering_service.FaceGroup") as MockGroup:
            new_group = MagicMock(id=uuid4())
            MockGroup.return_value = new_group

            mock_db.execute.side_effect = [
                mock_group_result,  # Get original group
                MagicMock(),  # Update faces
                mock_count_result,  # Get remaining count
            ]

            result = await clustering_service.split_group(
                db=mock_db,
                group_id=original_group_id,
                face_ids=face_ids,
                workspace_id=workspace_id,
            )

            assert "new_group_id" in result
            assert result["faces_moved"] == len(face_ids)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_split_group_validates_group_exists(
        self, clustering_service, mock_db
    ):
        """Test that split fails if group doesn't exist."""
        workspace_id = uuid4()
        group_id = uuid4()
        face_ids = [uuid4()]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Group not found"):
            await clustering_service.split_group(
                db=mock_db,
                group_id=group_id,
                face_ids=face_ids,
                workspace_id=workspace_id,
            )

    @pytest.mark.asyncio
    async def test_assign_to_group_joins_existing(
        self, clustering_service, mock_db
    ):
        """Test that new face joins existing similar group."""
        workspace_id = uuid4()
        face = MagicMock(id=uuid4(), group_id=None)
        embedding = np.random.randn(512).astype(np.float32)
        existing_group_id = uuid4()

        with patch(
            "src.app.services.clustering_service.embedding_service"
        ) as mock_embedding_service:
            mock_embedding_service.find_similar_faces = AsyncMock(
                return_value=[
                    {
                        "face_id": str(uuid4()),
                        "group_id": str(existing_group_id),
                        "distance": 0.1,
                    }
                ]
            )

            mock_db.execute.return_value = MagicMock()

            result = await clustering_service.assign_to_group(
                db=mock_db,
                face=face,
                embedding=embedding,
                workspace_id=workspace_id,
            )

            assert result == existing_group_id
            assert face.group_id == existing_group_id

    @pytest.mark.asyncio
    async def test_assign_to_group_creates_new_when_no_similar(
        self, clustering_service, mock_db
    ):
        """Test that new face creates new group when no similar faces."""
        workspace_id = uuid4()
        face = MagicMock(id=uuid4(), group_id=None)
        embedding = np.random.randn(512).astype(np.float32)

        with patch(
            "src.app.services.clustering_service.embedding_service"
        ) as mock_embedding_service:
            mock_embedding_service.find_similar_faces = AsyncMock(return_value=[])

            with patch(
                "src.app.services.clustering_service.FaceGroup"
            ) as MockGroup:
                new_group = MagicMock(id=uuid4())
                MockGroup.return_value = new_group

                result = await clustering_service.assign_to_group(
                    db=mock_db,
                    face=face,
                    embedding=embedding,
                    workspace_id=workspace_id,
                )

                assert result == new_group.id
                mock_db.add.assert_called()


class TestClusteringAlgorithm:
    """Tests for clustering algorithm parameters."""

    @pytest.fixture
    def clustering_service(self):
        """Create clustering service instance."""
        return ClusteringService()

    def test_dbscan_parameters_configured(self, clustering_service):
        """Test DBSCAN parameters are configured."""
        assert hasattr(clustering_service, "eps")
        assert hasattr(clustering_service, "min_samples")
        assert 0 < clustering_service.eps < 1
        assert clustering_service.min_samples >= 1

    def test_find_representative_selects_centroid_closest(
        self, clustering_service
    ):
        """Test representative selection finds face closest to centroid."""
        # Create embeddings with one clearly central
        embeddings = np.array([
            [0.0, 0.0],
            [0.1, 0.1],
            [-0.1, -0.1],
            [1.0, 1.0],  # Outlier
        ])
        face_ids = [uuid4() for _ in range(4)]

        # The centroid is approximately (0.25, 0.25)
        # Face at index 1 (0.1, 0.1) should be closest

        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            clustering_service._find_representative(embeddings, face_ids)
        )

        # Should return one of the central faces (not the outlier)
        assert result in face_ids[:3]
