"""Face service configuration using Pydantic Settings."""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Type-safe configuration for face-service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Service metadata
    SERVICE_NAME: str = Field(default="face-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    APP_ENV: str = Field(default="development")
    PORT: int = Field(default=8002)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://RawDrive_user:RawDrive_pass@postgres:5432/RawDrive_db"
    )

    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    REDIS_MAX_CONNECTIONS: int = Field(default=50)
    REDIS_CONNECT_TIMEOUT: int = Field(default=5)
    REDIS_READ_TIMEOUT: int = Field(default=10)

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="kafka:9092")
    KAFKA_CONSUMER_GROUP_ID: str = Field(default="face-service-group")
    KAFKA_AUTO_OFFSET_RESET: str = Field(default="earliest")
    KAFKA_ENABLE_AUTO_COMMIT: bool = Field(default=False)

    # Google Cloud Vision
    GOOGLE_CLOUD_VISION_CREDENTIALS: Optional[str] = Field(default=None)
    GOOGLE_CLOUD_VISION_PROJECT_ID: Optional[str] = Field(default=None)
    GOOGLE_CLOUD_VISION_ENABLED: bool = Field(default=False)

    # Face Detection Configuration
    FACE_DETECTION_RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    FACE_DETECTION_MIN_CONFIDENCE: float = Field(default=0.7)
    FACE_EMBEDDING_DIMENSION: int = Field(default=512)

    # Clustering Configuration
    DBSCAN_EPS: float = Field(default=0.5)  # Cosine distance threshold
    DBSCAN_MIN_SAMPLES: int = Field(default=2)

    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(default=5)
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = Field(default=60)

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


# Global settings instance
settings = Settings()
