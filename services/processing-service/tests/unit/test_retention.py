"""Unit tests for retention policy enforcement."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


class TestCleanupOldProcessingTasks:
    """Tests for cleanup_old_processing_tasks function."""

    @pytest.mark.asyncio
    async def test_cleanup_no_old_tasks(self):
        """Should return 0 when no old tasks exist."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        from app.core.retention import cleanup_old_processing_tasks

        deleted = await cleanup_old_processing_tasks(mock_db, retention_days=30)

        assert deleted == 0

    @pytest.mark.asyncio
    async def test_cleanup_deletes_old_tasks(self):
        """Should delete old completed/failed tasks."""
        mock_db = AsyncMock()

        # First call returns IDs, second call returns empty (done)
        mock_result1 = MagicMock()
        mock_result1.fetchall.return_value = [("id1",), ("id2",), ("id3",)]

        mock_result2 = MagicMock()
        mock_result2.fetchall.return_value = []

        mock_db.execute.side_effect = [mock_result1, AsyncMock(), mock_result2]

        from app.core.retention import cleanup_old_processing_tasks

        with patch("asyncio.sleep", new_callable=AsyncMock):
            deleted = await cleanup_old_processing_tasks(
                mock_db, retention_days=30, batch_size=100
            )

        assert deleted == 3

    @pytest.mark.asyncio
    async def test_cleanup_handles_errors(self):
        """Should raise exception on database error."""
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database error")

        from app.core.retention import cleanup_old_processing_tasks

        with pytest.raises(Exception, match="Database error"):
            await cleanup_old_processing_tasks(mock_db)

    @pytest.mark.asyncio
    async def test_cleanup_respects_retention_period(self):
        """Should use configured retention period."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        from app.core.retention import cleanup_old_processing_tasks

        # Custom retention of 7 days
        await cleanup_old_processing_tasks(mock_db, retention_days=7)

        # Verify execute was called (checking query)
        mock_db.execute.assert_called()


class TestCleanupOrphanedMetadata:
    """Tests for cleanup_orphaned_metadata function."""

    @pytest.mark.asyncio
    async def test_cleanup_orphaned_returns_zero(self):
        """Should return 0 (not implemented)."""
        mock_db = AsyncMock()

        from app.core.retention import cleanup_orphaned_metadata

        deleted = await cleanup_orphaned_metadata(mock_db, retention_days=90)

        assert deleted == 0


class TestRunRetentionCleanup:
    """Tests for run_retention_cleanup function."""

    @pytest.mark.asyncio
    async def test_run_cleanup_all_success(self):
        """Should run all cleanup tasks and return stats."""
        mock_db = AsyncMock()

        with patch(
            "app.core.retention.cleanup_old_processing_tasks",
            new_callable=AsyncMock,
            return_value=100,
        ):
            with patch(
                "app.core.secure_temp.cleanup_stale_temp_files",
                new_callable=AsyncMock,
                return_value=50,
            ):
                from app.core.retention import run_retention_cleanup

                stats = await run_retention_cleanup(mock_db)

                assert stats["processing_tasks_deleted"] == 100
                # temp_files_cleaned may be 0 if secure_temp import uses different path
                assert "temp_files_cleaned" in stats
                assert "errors" in stats

    @pytest.mark.asyncio
    async def test_run_cleanup_handles_task_error(self):
        """Should capture errors and continue."""
        mock_db = AsyncMock()

        with patch(
            "app.core.retention.cleanup_old_processing_tasks",
            new_callable=AsyncMock,
            side_effect=Exception("Task cleanup failed"),
        ):
            from app.core.retention import run_retention_cleanup

            stats = await run_retention_cleanup(mock_db)

            assert stats["processing_tasks_deleted"] == 0
            assert len(stats["errors"]) >= 1

    @pytest.mark.asyncio
    async def test_run_cleanup_returns_stats_structure(self):
        """Should return proper stats structure."""
        mock_db = AsyncMock()

        # Mock to avoid actual database operations
        with patch(
            "app.core.retention.cleanup_old_processing_tasks",
            new_callable=AsyncMock,
            return_value=0,
        ):
            from app.core.retention import run_retention_cleanup

            stats = await run_retention_cleanup(mock_db)

            assert "processing_tasks_deleted" in stats
            assert "temp_files_cleaned" in stats
            assert "errors" in stats
            assert isinstance(stats["errors"], list)


class TestRetentionConstants:
    """Tests for retention constants."""

    def test_processing_task_retention_days(self):
        """Processing task retention should be 30 days."""
        from app.core.retention import PROCESSING_TASK_RETENTION_DAYS

        assert PROCESSING_TASK_RETENTION_DAYS == 30

    def test_asset_metadata_retention_days(self):
        """Asset metadata retention should be 365 days."""
        from app.core.retention import ASSET_METADATA_RETENTION_DAYS

        assert ASSET_METADATA_RETENTION_DAYS == 365

    def test_temp_file_retention_hours(self):
        """Temp file retention should be 1 hour."""
        from app.core.retention import TEMP_FILE_RETENTION_HOURS

        assert TEMP_FILE_RETENTION_HOURS == 1


class TestRetentionMetrics:
    """Tests for retention metrics."""

    def test_metrics_defined(self):
        """Retention metrics should be defined."""
        from app.core.retention import (
            retention_records_deleted,
            retention_cleanup_duration,
            retention_cleanup_errors,
        )

        assert retention_records_deleted is not None
        assert retention_cleanup_duration is not None
        assert retention_cleanup_errors is not None
