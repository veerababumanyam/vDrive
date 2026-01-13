"""
vDrive Onboarding Service Configuration

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
    SERVICE_NAME: str = "onboarding-service"
    SERVICE_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # ===========================================
    # Server Configuration
    # ===========================================
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8006, description="Server port")

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
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry in days")

    # ===========================================
    # Email Verification
    # ===========================================
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = Field(
        default=24,
        description="Email verification token expiry in hours",
    )
    EMAIL_FROM: str = Field(
        default="noreply@vdrive.io",
        description="From address for verification emails",
    )

    # ===========================================
    # Password Security (Argon2id)
    # ===========================================
    ARGON2_TIME_COST: int = Field(default=3, ge=1, description="Argon2 time cost iterations")
    ARGON2_MEMORY_COST: int = Field(default=65536, ge=1024, description="Argon2 memory cost in KB")
    ARGON2_PARALLELISM: int = Field(default=4, ge=1, description="Argon2 parallelism factor")

    # ===========================================
    # Google OAuth
    # ===========================================
    GOOGLE_CLIENT_ID: str = Field(default="", description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", description="Google OAuth client secret")
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:8006/api/v1/onboarding/oauth/google/callback",
        description="Google OAuth redirect URI",
    )

    # ===========================================
    # Cloudflare Turnstile (Bot Protection)
    # ===========================================
    CLOUDFLARE_TURNSTILE_SECRET: str = Field(
        default="",
        description="Cloudflare Turnstile secret key",
    )
    CLOUDFLARE_TURNSTILE_VERIFY_URL: str = Field(
        default="https://challenges.cloudflare.com/turnstile/v0/siteverify",
        description="Turnstile verification endpoint",
    )

    # ===========================================
    # Kafka Event Bus
    # ===========================================
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers",
    )
    KAFKA_PRODUCER_TIMEOUT_MS: int = Field(default=10000, description="Kafka producer timeout")
    KAFKA_TOPIC_USER_REGISTERED: str = Field(default="user.registered", description="Topic for user registration events")
    KAFKA_TOPIC_EMAIL_VERIFIED: str = Field(default="user.email.verified", description="Topic for email verification events")
    KAFKA_TOPIC_WORKSPACE_CREATED: str = Field(default="workspace.created", description="Topic for workspace creation events")
    KAFKA_TOPIC_ONBOARDING_COMPLETED: str = Field(default="onboarding.completed", description="Topic for onboarding completion events")

    # ===========================================
    # External Services
    # ===========================================
    NOTIFICATION_SERVICE_URL: str = Field(
        default="http://localhost:8005",
        description="Notification service URL for sending emails",
    )
    BILLING_SERVICE_URL: str = Field(
        default="http://localhost:8013",
        description="Billing service URL for trial provisioning",
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
    RATE_LIMIT_REGISTRATION_MAX: int = Field(default=5, description="Max registrations per IP per window")
    RATE_LIMIT_REGISTRATION_WINDOW_SECONDS: int = Field(default=900, description="Registration rate limit window (15 min)")
    RATE_LIMIT_RESEND_MAX: int = Field(default=3, description="Max resend requests per user per window")
    RATE_LIMIT_RESEND_WINDOW_SECONDS: int = Field(default=3600, description="Resend rate limit window (1 hour)")
    RATE_LIMIT_SLUG_CHECK_MAX: int = Field(default=100, description="Max slug checks per minute")
    RATE_LIMIT_SLUG_CHECK_WINDOW_SECONDS: int = Field(default=60, description="Slug check rate limit window")

    # ===========================================
    # Trial Configuration
    # ===========================================
    TRIAL_DURATION_DAYS: int = Field(default=14, description="Trial period in days")
    TRIAL_STORAGE_GB: int = Field(default=100, description="Trial storage limit in GB")
    TRIAL_AI_CREDITS: int = Field(default=500, description="Trial AI credits")
    TRIAL_TIER: str = Field(default="pro", description="Trial subscription tier")

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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Singleton settings instance
settings = get_settings()
