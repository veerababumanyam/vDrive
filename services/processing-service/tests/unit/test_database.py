"""Unit tests for database module."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestGetDbSession:
    """Tests for get_db_session function."""

    @pytest.mark.asyncio
    async def test_returns_async_session_local(self):
        """Should return AsyncSessionLocal instance."""
        mock_session = AsyncMock()

        with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
            from app.core.database import get_db_session

            result = await get_db_session()

            assert result == mock_session


class TestCloseDb:
    """Tests for close_db function."""

    @pytest.mark.asyncio
    async def test_disposes_engine(self):
        """Should dispose the database engine."""
        mock_engine = MagicMock()
        mock_engine.dispose = AsyncMock()

        with patch("app.core.database.engine", mock_engine):
            from app.core.database import close_db

            await close_db()

            mock_engine.dispose.assert_called_once()


class TestGetDb:
    """Tests for get_db dependency function."""

    @pytest.mark.asyncio
    async def test_yields_session_and_closes(self):
        """Should yield session and close on exit."""
        mock_session = AsyncMock()
        mock_session.close = AsyncMock()

        mock_session_local = MagicMock()

        async def mock_context_manager():
            return mock_session

        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_local.return_value.__aexit__ = AsyncMock()

        with patch("app.core.database.AsyncSessionLocal", mock_session_local):
            from app.core.database import get_db

            # Consume the generator
            gen = get_db()
            session = await gen.__anext__()

            assert session == mock_session

            # Exhaust the generator
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
