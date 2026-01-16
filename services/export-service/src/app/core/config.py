"""
vDrive Export Service Configuration

Pydantic Settings for type-safe configuration from environment variables.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ===========================================
    # Service Identity
    # ===========================================
    SERVICE_NAME: str = "export-service"
    SERVICE_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # ===========================================
    # Server Configuration
    # ===========================================
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8023, description="Server port")

    # ===========================================
    # Database Configuration
    # ===========================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://vDrive:vDrive@localhost:5432/vDrive",
        description="PostgreSQL connection URL with asyncpg driver",
    )
    DB_POOL_MIN_SIZE: int = Field(default=2, ge=1, description="Minimum database pool size")
    DB_POOL_MAX_SIZE: int = Field(default=10, ge=1, description="Maximum database pool size")
    DB_POOL_MAX_LIFETIME_SEC: int = Field(default=1800, description="Connection max lifetime in seconds")
    DB_ECHO: bool = Field(default=False, description="Echo SQL statements for debugging")

    # ===========================================
    # Redis Configuration
    # ===========================================
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    REDIS_MAX_CONNECTIONS: int = Field(default=10, description="Max Redis connections")

    # ===========================================
    # JWT Authentication
    # ===========================================
    JWT_SECRET: str = Field(
        default="",
        description="JWT secret key for token signing",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_PRIVATE_KEY: Optional[str] = Field(default=None, description="EdDSA private key")
    JWT_PUBLIC_KEY: Optional[str] = Field(default=None, description="EdDSA public key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiry in minutes")

    # ===========================================
    # Kafka Event Bus
    # ===========================================
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers",
    )
    KAFKA_PRODUCER_TIMEOUT_MS: int = Field(default=10000, description="Kafka producer timeout")
    KAFKA_TOPIC_EXPORT_CREATED: str = Field(default="export.created", description="Topic for export creation events")
    KAFKA_TOPIC_EXPORT_COMPLETED: str = Field(default="export.completed", description="Topic for export completion events")
    KAFKA_TOPIC_EXPORT_FAILED: str = Field(default="export.failed", description="Topic for export failure events")
    KAFKA_TOPIC_MIGRATION_CREATED: str = Field(default="migration.created", description="Topic for migration creation events")
    KAFKA_TOPIC_MIGRATION_COMPLETED: str = Field(default="migration.completed", description="Topic for migration completion events")

    # ===========================================
    # Celery Configuration
    # ===========================================
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL (Redis)",
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL",
    )

    # ===========================================
    # Cloudflare R2 Storage
    # ===========================================
    R2_ENDPOINT_URL: str = Field(
        default="https://account-id.r2.cloudflarestorage.com",
        description="R2 endpoint URL",
    )
    R2_ACCESS_KEY_ID: str = Field(
        default="",
        description="R2 access key ID",
    )
    R2_SECRET_ACCESS_KEY: str = Field(
        default="",
        description="R2 secret access key",
    )
    R2_BUCKET_NAME: str = Field(
        default="vDrive-exports",
        description="R2 bucket name for exports",
    )
    R2_PUBLIC_URL: str = Field(
        default="https://exports.vdrive.io",
        description="Public URL for export downloads",
    )

    # ===========================================
    # Export Configuration
    # ===========================================
    MAX_EXPORT_SIZE_BYTES: int = Field(
        default=10737418240,  # 10GB
        description="Maximum export size in bytes",
    )
    EXPORT_RETENTION_HOURS: int = Field(
        default=72,  # 3 days
        description="Export file retention in hours",
    )
    MAX_CONCURRENT_EXPORTS: int = Field(
        default=2,
        description="Maximum concurrent export jobs per workspace",
    )

    # ===========================================
    # External Services
    # ===========================================
    BACKEND_SERVICE_URL: str = Field(
        default="http://localhost:8000",
        description="Backend service URL",
    )
    GALLERY_SERVICE_URL: str = Field(
        default="http://localhost:8004",
        description="Gallery service URL",
    )

    # ===========================================
    # Application URLs
    # ===========================================
    APP_URL: str = Field(
        default="https://app.vdrive.io",
        description="Frontend application URL",
    )
    WEBSITE_URL: str = Field(
        default="https://www.vdrive.io",
        description="Public website URL",
    )

    # ===========================================
    # Rate Limiting
    # ===========================================
    RATE_LIMIT_EXPORT_MAX: int = Field(default=5, description="Max export requests per user per window")
    RATE_LIMIT_EXPORT_WINDOW_SECONDS: int = Field(default=3600, description="Export rate limit window (1 hour)")

    # ===========================================
    # CORS Configuration
    # ===========================================
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "https://app.vdrive.io",
            "https://www.vdrive.io",
        ],
        description="Allowed CORS origins",
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses asyncpg driver."""
        if v and not v.startswith("postgresql+asyncpg://"):
            if v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """Ensure JWT secret is configured in production."""
        data = info.data
        if data.get("APP_ENV") == "production" and not v:
            raise ValueError("JWT_SECRET must be set in production")
        return v

    @field_validator("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    @classmethod
    def validate_r2_credentials(cls, v: str, info) -> str:
        """Ensure R2 credentials are configured in production."""
        data = info.data
        if data.get("APP_ENV") == "production" and not v:
            raise ValueError("R2 credentials must be set in production")
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.

    Use this function to access settings throughout the application.
    LRU cache ensures settings are loaded only once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
