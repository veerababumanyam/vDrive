"""vDrive Gallery Service Configuration"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Gallery Service settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Service Identity
    SERVICE_NAME: str = "gallery-service"
    SERVICE_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development")

    # Server Configuration
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8004)

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://vDrive:vDrive_dev_password@localhost:5432/vDrive"
    )
    DB_POOL_MIN_SIZE: int = Field(default=5)
    DB_POOL_MAX_SIZE: int = Field(default=20)
    DB_POOL_MAX_LIFETIME_SEC: int = Field(default=3600)
    DB_ECHO: bool = Field(default=False)

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS: int = Field(default=50)

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092")

    # Object Storage (R2/S3)
    R2_ACCESS_KEY_ID: str = Field(default="")
    R2_SECRET_ACCESS_KEY: str = Field(default="")
    R2_BUCKET_NAME: str = Field(default="vDrive")
    R2_ENDPOINT_URL: str = Field(default="")
    R2_REGION: str = Field(default="auto")

    # JWT Configuration (for staff endpoints)
    JWT_SECRET: str = Field(default="your-secret-key-here-change-in-production")
    JWT_ALGORITHM: str = Field(default="EdDSA")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """Ensure JWT_SECRET is secure in production environments."""
        app_env = info.data.get("APP_ENV", "development") if info.data else "development"
        if app_env in ("production", "staging"):
            if not v or len(v) < 32:
                raise ValueError(
                    "JWT_SECRET must be at least 32 characters in production/staging environments"
                )
        return v

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:8020"]
    )

    # Rate Limiting
    RATE_LIMIT_PER_IP: int = Field(default=200)  # requests per minute
    RATE_LIMIT_PER_MAGIC_LINK: int = Field(default=100)  # requests per minute

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure DATABASE_URL uses async driver."""
        if v and "postgresql://" in v and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
