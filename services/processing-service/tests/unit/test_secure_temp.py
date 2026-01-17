"""Unit tests for secure temporary file handling."""

import os
import pytest
import time
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestGenerateSecureFilename:
    """Tests for generate_secure_filename function."""

    def test_generate_unique_filenames(self):
        """Should generate unique filenames."""
        from app.core.secure_temp import generate_secure_filename

        name1 = generate_secure_filename()
        name2 = generate_secure_filename()

        assert name1 != name2

    def test_generate_with_prefix(self):
        """Should include prefix in filename."""
        from app.core.secure_temp import generate_secure_filename

        name = generate_secure_filename(prefix="test")
        assert name.startswith("test_")

    def test_generate_with_suffix(self):
        """Should include suffix in filename."""
        from app.core.secure_temp import generate_secure_filename

        name = generate_secure_filename(suffix=".dat")
        assert name.endswith(".dat")

    def test_generate_with_prefix_and_suffix(self):
        """Should include both prefix and suffix."""
        from app.core.secure_temp import generate_secure_filename

        name = generate_secure_filename(prefix="img", suffix=".webp")
        assert name.startswith("img_")
        assert name.endswith(".webp")


class TestGetSecureTempBase:
    """Tests for get_secure_temp_base function."""

    def test_creates_directory(self):
        """Should create temp directory if it doesn't exist."""
        from app.core.secure_temp import get_secure_temp_base

        with patch("app.core.secure_temp._SECURE_TEMP_BASE", None):
            base = get_secure_temp_base()
            assert base is not None
            assert base.name == "processing-service"

    def test_returns_existing_base(self):
        """Should return existing base if already created."""
        from app.core.secure_temp import get_secure_temp_base

        base1 = get_secure_temp_base()
        base2 = get_secure_temp_base()

        # Should return same path
        assert str(base1) == str(base2)


class TestSecureTempFile:
    """Tests for secure_temp_file context manager."""

    def test_creates_temp_file(self):
        """Should create temporary file."""
        from app.core.secure_temp import secure_temp_file

        with secure_temp_file() as path:
            assert path.exists()
            assert path.is_file()

    def test_deletes_on_exit(self):
        """Should delete file on context exit."""
        from app.core.secure_temp import secure_temp_file

        with secure_temp_file() as path:
            filepath = path

        assert not filepath.exists()

    def test_no_delete_option(self):
        """Should not delete when delete=False."""
        from app.core.secure_temp import secure_temp_file

        with secure_temp_file(delete=False) as path:
            filepath = path

        try:
            assert filepath.exists()
        finally:
            # Clean up manually
            if filepath.exists():
                filepath.unlink()

    def test_custom_suffix(self):
        """Should use custom suffix."""
        from app.core.secure_temp import secure_temp_file

        with secure_temp_file(suffix=".webp") as path:
            assert str(path).endswith(".webp")

    def test_custom_prefix(self):
        """Should use custom prefix."""
        from app.core.secure_temp import secure_temp_file

        with secure_temp_file(prefix="thumb") as path:
            assert "thumb_" in path.name

    def test_file_has_secure_permissions(self):
        """File should have restricted permissions (0o600)."""
        from app.core.secure_temp import secure_temp_file

        with secure_temp_file() as path:
            mode = path.stat().st_mode & 0o777
            assert mode == 0o600


class TestSecureTempDir:
    """Tests for secure_temp_dir context manager."""

    def test_creates_temp_directory(self):
        """Should create temporary directory."""
        from app.core.secure_temp import secure_temp_dir

        with secure_temp_dir() as path:
            assert path.exists()
            assert path.is_dir()

    def test_deletes_on_exit(self):
        """Should delete directory on context exit."""
        from app.core.secure_temp import secure_temp_dir

        with secure_temp_dir() as path:
            dirpath = path

        assert not dirpath.exists()

    def test_deletes_with_contents(self):
        """Should delete directory with contents."""
        from app.core.secure_temp import secure_temp_dir

        with secure_temp_dir() as path:
            # Create some files inside
            (path / "file1.txt").write_text("test1")
            (path / "file2.txt").write_text("test2")
            dirpath = path

        assert not dirpath.exists()

    def test_directory_has_secure_permissions(self):
        """Directory should have restricted permissions (0o700)."""
        from app.core.secure_temp import secure_temp_dir

        with secure_temp_dir() as path:
            mode = path.stat().st_mode & 0o777
            assert mode == 0o700


class TestAsyncSecureTempFile:
    """Tests for async_secure_temp_file context manager."""

    @pytest.mark.asyncio
    async def test_creates_temp_file(self):
        """Should create temporary file."""
        from app.core.secure_temp import async_secure_temp_file

        async with async_secure_temp_file() as path:
            assert path.exists()
            assert path.is_file()

    @pytest.mark.asyncio
    async def test_deletes_on_exit(self):
        """Should delete file on context exit."""
        from app.core.secure_temp import async_secure_temp_file

        async with async_secure_temp_file() as path:
            filepath = path

        assert not filepath.exists()

    @pytest.mark.asyncio
    async def test_custom_suffix(self):
        """Should use custom suffix."""
        from app.core.secure_temp import async_secure_temp_file

        async with async_secure_temp_file(suffix=".dat") as path:
            assert str(path).endswith(".dat")


class TestCleanupStaleTempFiles:
    """Tests for cleanup_stale_temp_files function."""

    @pytest.mark.asyncio
    async def test_cleanup_old_files(self):
        """Should clean up files older than max_age."""
        from app.core.secure_temp import (
            secure_temp_file,
            cleanup_stale_temp_files,
            get_secure_temp_base,
        )

        # Create a temp file and make it appear old
        with secure_temp_file(delete=False) as path:
            filepath = path
            # Set modification time to 2 hours ago
            old_time = time.time() - 7200
            os.utime(filepath, (old_time, old_time))

        # Cleanup files older than 1 hour
        cleaned = await cleanup_stale_temp_files(max_age_seconds=3600)

        assert cleaned >= 1
        assert not filepath.exists()

    @pytest.mark.asyncio
    async def test_keeps_recent_files(self):
        """Should keep files newer than max_age."""
        from app.core.secure_temp import (
            secure_temp_file,
            cleanup_stale_temp_files,
        )

        with secure_temp_file(delete=False) as path:
            filepath = path

        # Cleanup files older than 1 hour - file is new
        cleaned = await cleanup_stale_temp_files(max_age_seconds=3600)

        # File should still exist (cleanup returns count of cleaned files)
        assert filepath.exists()

        # Clean up
        filepath.unlink()

    @pytest.mark.asyncio
    async def test_returns_zero_if_base_missing(self):
        """Should return 0 if base directory doesn't exist."""
        from app.core.secure_temp import cleanup_stale_temp_files

        with patch("app.core.secure_temp.get_secure_temp_base") as mock:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock.return_value = mock_path

            cleaned = await cleanup_stale_temp_files()
            assert cleaned == 0


class TestTempFileMetrics:
    """Tests for temp file metrics."""

    def test_metrics_defined(self):
        """Temp file metrics should be defined."""
        from app.core.secure_temp import (
            temp_files_created_total,
            temp_files_cleaned_total,
            temp_files_cleanup_errors_total,
            temp_files_active,
        )

        assert temp_files_created_total is not None
        assert temp_files_cleaned_total is not None
        assert temp_files_cleanup_errors_total is not None
        assert temp_files_active is not None
