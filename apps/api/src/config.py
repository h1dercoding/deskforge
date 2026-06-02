from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import json
import sys


# Known insecure default values that must not be used in production
_INSECURE_DEFAULTS = {
    "change-me-in-production",
    "change-me-jwt-secret-in-production",
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
}


class Settings(BaseSettings):
    """DeskForge application settings loaded from environment variables."""

    # Application
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"
    APP_SECRET_KEY: str = ""
    APP_CORS_ORIGINS: str = '["http://localhost:3000"]'

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://deskforge:password@localhost:5432/deskforge"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # Email
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@deskforge.io"

    # Encryption
    ENCRYPTION_KEY: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"
    SENTRY_DSN: str = ""

    # Rate Limiting
    RATE_LIMIT_API_PER_MINUTE: int = 100
    RATE_LIMIT_GENERATE_PER_MINUTE: int = 10

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.APP_CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000"]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def app_url(self) -> str:
        if self.is_production:
            return "https://app.deskforge.io"
        return "http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()


def _validate_settings() -> None:
    """Validate critical settings at startup. Raises SystemExit on misconfiguration."""
    errors = []

    # ENCRYPTION_KEY must be set and not be the default
    if not settings.ENCRYPTION_KEY:
        errors.append("ENCRYPTION_KEY is not set. Please set a 64-character hex key via the ENCRYPTION_KEY environment variable.")
    elif settings.ENCRYPTION_KEY in _INSECURE_DEFAULTS:
        errors.append("ENCRYPTION_KEY is set to a known insecure default. Please generate a unique key.")

    # JWT_SECRET_KEY must be set and not be a default
    if not settings.JWT_SECRET_KEY:
        errors.append("JWT_SECRET_KEY is not set. Please set a strong secret via the JWT_SECRET_KEY environment variable.")
    elif settings.JWT_SECRET_KEY in _INSECURE_DEFAULTS:
        errors.append("JWT_SECRET_KEY is set to a known insecure default. Please set a unique secret.")

    # APP_SECRET_KEY must be set and not be a default
    if not settings.APP_SECRET_KEY:
        errors.append("APP_SECRET_KEY is not set. Please set a strong secret via the APP_SECRET_KEY environment variable.")
    elif settings.APP_SECRET_KEY in _INSECURE_DEFAULTS:
        errors.append("APP_SECRET_KEY is set to a known insecure default. Please set a unique secret.")

    if errors:
        import logging
        logger = logging.getLogger("deskforge.config")
        for error in errors:
            logger.error(f"CONFIGURATION ERROR: {error}")
        if settings.is_production:
            sys.exit(1)
        else:
            logger.warning("Running in non-production mode with insecure configuration. DO NOT deploy to production.")


# Run validation on import (fail fast)
_validate_settings()
