"""AI Search service configuration using Pydantic Settings."""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Type-safe configuration for ai-search-service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Service metadata
    SERVICE_NAME: str = Field(default="ai-search-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    APP_ENV: str = Field(default="development")
    PORT: int = Field(default=8009)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://vdrive_user:vdrive_pass@postgres:5432/vdrive_db"
    )

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="kafka:9092")
    KAFKA_CONSUMER_GROUP_ID: str = Field(default="ai-search-service-group")
    KAFKA_AUTO_OFFSET_RESET: str = Field(default="earliest")
    KAFKA_ENABLE_AUTO_COMMIT: bool = Field(default=False)

    # CLIP Model Configuration
    CLIP_MODEL: str = Field(default="clip-ViT-L-14")
    CLIP_EMBEDDING_DIMENSION: int = Field(default=1536)
    CLIP_MAX_BATCH_SIZE: int = Field(default=32)

    # Gemini LLM Configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash")
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(default=2048)
    GEMINI_TEMPERATURE: float = Field(default=0.7)

    # RAG Configuration
    RAG_MAX_CONTEXT_PHOTOS: int = Field(default=10)
    RAG_SIMILARITY_THRESHOLD: float = Field(default=0.7)

    # Search Configuration
    SEARCH_DEFAULT_LIMIT: int = Field(default=50)
    SEARCH_MAX_LIMIT: int = Field(default=200)

    # Caption Configuration
    CAPTION_STYLES: list[str] = Field(
        default=["professional", "casual", "seo", "social_media"]
    )
    CAPTION_MAX_LENGTH: int = Field(default=500)

    # Observability
    SENTRY_DSN: Optional[str] = Field(default=None)
    PROMETHEUS_ENABLED: bool = Field(default=True)

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure DATABASE_URL is not empty."""
        if not v or v == "":
            raise ValueError("DATABASE_URL must be set")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == "production"

    @property
    def gemini_enabled(self) -> bool:
        """Check if Gemini is configured."""
        return bool(self.GEMINI_API_KEY)


# Global settings instance
settings = Settings()
