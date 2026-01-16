"""
Configuration settings for Upload Service.

Uses Pydantic Settings for type-safe configuration with environment variable support.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Upload Service configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Service Identity
    SERVICE_NAME: str = Field(default="upload-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    APP_ENV: str = Field(default="development")

    # Server Configuration
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8008)
    API_BASE_URL: str = Field(default="http://localhost:8008")

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://RawDrive:RawDrive_dev_password@localhost:5432/RawDrive"
    )
    DB_POOL_MIN_SIZE: int = Field(default=5)
    DB_POOL_MAX_SIZE: int = Field(default=20)
    DB_POOL_MAX_LIFETIME_SEC: int = Field(default=1800)
    DB_ECHO: bool = Field(default=False)

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS: int = Field(default=50)

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092")

    # R2 Storage Configuration
    R2_ACCESS_KEY_ID: str = Field(default="")
    R2_SECRET_ACCESS_KEY: str = Field(default="")
    R2_BUCKET_NAME: str = Field(default="RawDrive")
    R2_ENDPOINT: str = Field(default="")

    # JWT Authentication
    JWT_SECRET: str = Field(default="")
    JWT_ALGORITHM: str = Field(default="HS256")  # Must match onboarding-service

    # Encryption Configuration
    ENCRYPTION_MASTER_KEY: str = Field(default="")

    # TUS Configuration
    TUS_MAX_SIZE: int = Field(default=10737418240)  # 10GB
    TUS_UPLOAD_URL_TTL_HOURS: int = Field(default=24)
    MAX_CONCURRENT_UPLOADS_PER_WORKSPACE: int = Field(default=10)

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8000",
        ]
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure DATABASE_URL uses async driver."""
        if "postgresql://" in v and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """Ensure JWT_SECRET is secure in production."""
        app_env = info.data.get("APP_ENV", "development")
        if app_env in ("production", "staging"):
            if not v or len(v) < 32:
                raise ValueError("JWT_SECRET must be at least 32 characters in production")
        return v

    @field_validator("ENCRYPTION_MASTER_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str, info) -> str:
        """Ensure ENCRYPTION_MASTER_KEY is secure."""
        app_env = info.data.get("APP_ENV", "development")
        if app_env in ("production", "staging"):
            if not v or len(v) < 32:
                raise ValueError("ENCRYPTION_MASTER_KEY must be at least 32 characters")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
