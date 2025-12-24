"""Configuration management using Pydantic Settings."""

import os
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Weatherstack API configuration
    WEATHERSTACK_API_KEY: str
    WEATHERSTACK_BASE_URL: str = "http://api.weatherstack.com"

    # Cache configuration
    CACHE_TTL_SECONDS: int = 300  # 5 minutes default
    STALE_CACHE_MAX_AGE_SECONDS: int = 3600  # 1 hour for stale cache fallback

    # Rate limiting configuration
    RATE_LIMIT_PER_MINUTE: int = 60

    # Retry configuration
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_BACKOFF_BASE: float = 1.0  # seconds

    # Circuit breaker configuration
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5  # consecutive failures
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60  # seconds
    CIRCUIT_BREAKER_FAILURE_RATE_THRESHOLD: float = 0.5  # 50%

    # HTTP timeout configuration
    HTTP_CONNECT_TIMEOUT: float = 3.0  # seconds
    HTTP_READ_TIMEOUT: float = 5.0  # seconds
    HTTP_TOTAL_TIMEOUT: float = 8.0  # seconds

    # Logging configuration
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    print("=" * 60, file=sys.stderr)
    print("ERROR: Configuration validation failed!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"\nMissing required environment variable: WEATHERSTACK_API_KEY", file=sys.stderr)
    print("\nTo fix this:", file=sys.stderr)
    print("1. Create a .env file with: WEATHERSTACK_API_KEY=your_api_key", file=sys.stderr)
    print("2. Or set environment variable: export WEATHERSTACK_API_KEY=your_api_key", file=sys.stderr)
    print("3. Or pass it to Docker: docker run -e WEATHERSTACK_API_KEY=your_api_key ...", file=sys.stderr)
    print("\nGet your free API key at: https://weatherstack.com/signup/free", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    sys.exit(1)

