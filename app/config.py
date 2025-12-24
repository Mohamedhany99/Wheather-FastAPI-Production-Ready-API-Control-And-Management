"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Weatherstack API configuration
    WEATHERSTACK_API_KEY: str
    WEATHERSTACK_BASE_URL: str = "http://api.weatherstack.com"

    # Cache configuration
    CACHE_TTL_SECONDS: int = 300  # 5 minutes default

    # Rate limiting configuration
    RATE_LIMIT_PER_MINUTE: int = 60

    # Logging configuration
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()

