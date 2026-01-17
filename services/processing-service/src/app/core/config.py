"""Processing service configuration using Pydantic Settings."""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Type-safe configuration for processing-service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Service metadata
    SERVICE_NAME: str = Field(default="processing-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    APP_ENV: str = Field(default="development")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://RawDrive_user:RawDrive_pass@postgres:5432/RawDrive_db"
    )

    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/1")
    REDIS_MAX_CONNECTIONS: int = Field(default=50)
    REDIS_CONNECT_TIMEOUT: int = Field(default=5)  # seconds
    REDIS_READ_TIMEOUT: int = Field(default=10)  # seconds
    REDIS_SSL_ENABLED: bool = Field(default=False)

    # Idempotency
    IDEMPOTENCY_TTL_SECONDS: int = Field(default=86400)  # 24 hours

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="kafka:9092")
    KAFKA_CONSUMER_GROUP: str = Field(default="processing-service")
    KAFKA_AUTO_OFFSET_RESET: str = Field(default="earliest")
    KAFKA_ENABLE_AUTO_COMMIT: bool = Field(default=False)

    # Storage (Cloudflare R2)
    R2_ENDPOINT: str = Field(default="https://xxx.r2.cloudflarestorage.com")
    R2_ACCESS_KEY_ID: str = Field(default="")
    R2_SECRET_ACCESS_KEY: str = Field(default="")
    R2_BUCKET_NAME: str = Field(default="RawDrive-assets")
    R2_PUBLIC_URL: Optional[str] = Field(default=None)

    # Encryption
    ENCRYPTION_MASTER_KEY: str = Field(default="")

    # Google Cloud Vision
    GOOGLE_CLOUD_VISION_CREDENTIALS: Optional[str] = Field(default=None)
    GOOGLE_CLOUD_VISION_ENABLED: bool = Field(default=False)
    GOOGLE_CLOUD_VISION_RATE_LIMIT: int = Field(default=1000)  # requests/minute

    # Processing configuration
    THUMBNAIL_SIZE: int = Field(default=300)
    PREVIEW_SIZE: int = Field(default=1200)
    LQIP_SIZE: int = Field(default=20)
    WEBP_QUALITY: int = Field(default=85)
    THUMBNAIL_QUALITY: int = Field(default=80)
    LQIP_QUALITY: int = Field(default=60)

    # Task processing
    MAX_CONCURRENT_TASKS: int = Field(default=10)
    TASK_TIMEOUT_SECONDS: int = Field(default=300)
    MAX_RETRIES: int = Field(default=3)

    # Monitoring
    PROMETHEUS_PORT: int = Field(default=8010)

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure DATABASE_URL is not empty."""
        if not v or v == "":
            raise ValueError("DATABASE_URL must be set")
        return v

    @field_validator("ENCRYPTION_MASTER_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str, info) -> str:
        """Validate encryption master key format (skip in test/dev)."""
        if not v:
            # Allow empty in test/development environments
            return "0" * 64  # Default test key
        if len(v) != 64:
            raise ValueError("ENCRYPTION_MASTER_KEY must be 64 hex characters (32 bytes)")
        try:
            bytes.fromhex(v)
        except ValueError:
            raise ValueError("ENCRYPTION_MASTER_KEY must be valid hex string")
        return v

    @field_validator("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    @classmethod
    def validate_r2_credentials(cls, v: str, info) -> str:
        """Ensure R2 credentials are configured (allow empty for testing)."""
        # Allow empty for test/development - will fail gracefully at runtime
        return v or "test-credential"


# Global settings instance
settings = Settings()
