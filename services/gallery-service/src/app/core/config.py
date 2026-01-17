"""
vDrive Gallery Service Configuration

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
    SERVICE_NAME: str = "gallery-service"
    SERVICE_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # ===========================================
    # Server Configuration
    # ===========================================
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8004, description="Server port")

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

    # ===========================================
    # Cloudflare R2 Storage
    # ===========================================
    R2_ENDPOINT: str = Field(
        default="",
        description="Cloudflare R2 endpoint URL",
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
        default="vdrive-gallery",
        description="R2 bucket name for gallery storage",
    )
    R2_PUBLIC_URL: str = Field(
        default="",
        description="Public CDN URL for R2 bucket",
    )

    # ===========================================
    # Image Processing
    # ===========================================
    MAX_IMAGE_SIZE_MB: int = Field(default=50, description="Maximum image size in MB")
    THUMBNAIL_SIZES: List[int] = Field(
        default=[150, 300, 600, 1200],
        description="Thumbnail sizes to generate (width in pixels)",
    )
    WATERMARK_OPACITY: float = Field(default=0.5, ge=0.0, le=1.0, description="Default watermark opacity")
    MAX_BATCH_SIZE: int = Field(default=1000, description="Maximum photos in a batch operation")

    # ===========================================
    # Kafka Event Bus
    # ===========================================
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers",
    )
    KAFKA_PRODUCER_TIMEOUT_MS: int = Field(default=10000, description="Kafka producer timeout")
    KAFKA_TOPIC_GALLERY_CREATED: str = Field(default="gallery.created", description="Topic for gallery creation events")
    KAFKA_TOPIC_GALLERY_UPDATED: str = Field(default="gallery.updated", description="Topic for gallery update events")
    KAFKA_TOPIC_GALLERY_DELETED: str = Field(default="gallery.deleted", description="Topic for gallery deletion events")
    KAFKA_TOPIC_GALLERY_PUBLISHED: str = Field(default="gallery.published", description="Topic for gallery publish events")
    KAFKA_TOPIC_PHOTO_UPLOADED: str = Field(default="photo.uploaded", description="Topic for photo upload events")
    KAFKA_TOPIC_PHOTO_DELETED: str = Field(default="photo.deleted", description="Topic for photo deletion events")
    KAFKA_TOPIC_WATERMARK_APPLIED: str = Field(default="watermark.applied", description="Topic for watermark application events")

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
    RATE_LIMIT_UPLOAD_MAX: int = Field(default=100, description="Max uploads per workspace per window")
    RATE_LIMIT_UPLOAD_WINDOW_SECONDS: int = Field(default=3600, description="Upload rate limit window (1 hour)")
    RATE_LIMIT_WATERMARK_MAX: int = Field(default=10, description="Max watermark operations per workspace per window")
    RATE_LIMIT_WATERMARK_WINDOW_SECONDS: int = Field(default=300, description="Watermark rate limit window (5 min)")

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
        """Warn if JWT secret is empty in non-dev environments."""
        app_env = info.data.get("APP_ENV", "development")
        if app_env != "development" and not v:
            raise ValueError("JWT_SECRET must be set in non-development environments")
        return v

    @field_validator("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    @classmethod
    def validate_r2_credentials(cls, v: str, info) -> str:
        """Warn if R2 credentials are empty in non-dev environments."""
        app_env = info.data.get("APP_ENV", "development")
        if app_env != "development" and not v:
            raise ValueError("R2 credentials must be set in non-development environments")
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Use this function to access settings throughout the application.
    Settings are cached for performance.
    """
    return Settings()


# Global settings instance
settings = get_settings()
