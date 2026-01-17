"""Tests for configuration settings and validators."""

import pytest
from pydantic import ValidationError


class TestSettingsValidation:
    """Test Settings validation logic."""

    def test_jwt_secret_validation_production_too_short(self):
        """Test JWT_SECRET validation fails in production with short secret."""
        from src.app.core.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings(
                APP_ENV="production",
                JWT_SECRET="short",  # Less than 32 characters
                R2_ACCESS_KEY_ID="test",
                R2_SECRET_ACCESS_KEY="test",
                R2_ENDPOINT="https://test.r2.cloudflarestorage.com",
            )

        assert "JWT_SECRET must be at least 32 characters" in str(exc_info.value)

    def test_jwt_secret_validation_staging_too_short(self):
        """Test JWT_SECRET validation fails in staging with short secret."""
        from src.app.core.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings(
                APP_ENV="staging",
                JWT_SECRET="also-too-short",  # Less than 32 characters
                R2_ACCESS_KEY_ID="test",
                R2_SECRET_ACCESS_KEY="test",
                R2_ENDPOINT="https://test.r2.cloudflarestorage.com",
            )

        assert "JWT_SECRET must be at least 32 characters" in str(exc_info.value)

    def test_jwt_secret_validation_production_valid(self):
        """Test JWT_SECRET validation passes in production with long secret."""
        from src.app.core.config import Settings

        # Should not raise exception with 32+ character secret
        settings = Settings(
            APP_ENV="production",
            JWT_SECRET="a" * 32,  # Exactly 32 characters
            R2_ACCESS_KEY_ID="test",
            R2_SECRET_ACCESS_KEY="test",
            R2_ENDPOINT="https://test.r2.cloudflarestorage.com",
        )

        assert settings.JWT_SECRET == "a" * 32

    def test_jwt_secret_validation_development_allows_short(self):
        """Test JWT_SECRET validation allows short secret in development."""
        from src.app.core.config import Settings

        # Should not raise exception in development even with short secret
        settings = Settings(
            APP_ENV="development",
            JWT_SECRET="dev-secret",  # Less than 32 characters
            R2_ACCESS_KEY_ID="test",
            R2_SECRET_ACCESS_KEY="test",
            R2_ENDPOINT="https://test.r2.cloudflarestorage.com",
        )

        assert settings.JWT_SECRET == "dev-secret"

    def test_database_url_auto_adds_asyncpg(self):
        """Test DATABASE_URL validator auto-adds +asyncpg driver."""
        from src.app.core.config import Settings

        settings = Settings(
            DATABASE_URL="postgresql://user:pass@localhost:5432/RawDrive",
            R2_ACCESS_KEY_ID="test",
            R2_SECRET_ACCESS_KEY="test",
            R2_ENDPOINT="https://test.r2.cloudflarestorage.com",
        )

        # Should auto-convert to asyncpg
        assert "+asyncpg" in settings.DATABASE_URL
        assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/RawDrive"

    def test_database_url_preserves_existing_asyncpg(self):
        """Test DATABASE_URL validator preserves existing +asyncpg."""
        from src.app.core.config import Settings

        settings = Settings(
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/RawDrive",
            R2_ACCESS_KEY_ID="test",
            R2_SECRET_ACCESS_KEY="test",
            R2_ENDPOINT="https://test.r2.cloudflarestorage.com",
        )

        # Should not duplicate +asyncpg
        assert settings.DATABASE_URL.count("+asyncpg") == 1
        assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/RawDrive"

    def test_settings_default_values(self):
        """Test Settings loads with default values."""
        from src.app.core.config import Settings

        # Create settings with minimal required fields
        settings = Settings(
            R2_ACCESS_KEY_ID="test",
            R2_SECRET_ACCESS_KEY="test",
            R2_ENDPOINT="https://test.r2.cloudflarestorage.com",
        )

        # Check some defaults (note: some may be overridden by env vars)
        assert settings.SERVICE_NAME == "gallery-service"
        assert settings.SERVICE_VERSION == "1.0.0"
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8004
        assert settings.DB_POOL_MIN_SIZE == 5
        assert settings.DB_POOL_MAX_SIZE == 20
        assert settings.REDIS_MAX_CONNECTIONS == 50
        # JWT_ALGORITHM may be overridden by env vars - just check it's a valid algorithm
        assert settings.JWT_ALGORITHM in ["EdDSA", "HS256", "RS256", "ES256"]
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 15

    def test_settings_cors_origins_default(self):
        """Test CORS_ORIGINS has correct default values."""
        from src.app.core.config import Settings

        settings = Settings(
            R2_ACCESS_KEY_ID="test",
            R2_SECRET_ACCESS_KEY="test",
            R2_ENDPOINT="https://test.r2.cloudflarestorage.com",
        )

        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:5173" in settings.CORS_ORIGINS
        assert "http://localhost:8020" in settings.CORS_ORIGINS
