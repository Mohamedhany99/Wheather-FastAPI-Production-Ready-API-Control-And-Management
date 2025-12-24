"""Response models with metadata for API responses."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ResponseMetadata(BaseModel):
    """Metadata about the response source and freshness."""

    cached: bool = Field(description="Whether the data came from cache")
    stale: bool = Field(description="Whether the data is stale (expired cache)")
    age_seconds: float = Field(description="Age of the data in seconds")
    source: str = Field(description="Source of data: 'api', 'cache', 'cache_fallback'")
    retry_attempts: int = Field(default=0, description="Number of retry attempts made")
    circuit_breaker_state: Optional[str] = Field(
        default=None, description="Circuit breaker state: 'closed', 'open', 'half_open'"
    )


class WeatherResponse(BaseModel):
    """Weather API response with data and metadata."""

    data: Dict[str, Any] = Field(description="Weather data from Weatherstack API")
    metadata: ResponseMetadata = Field(description="Response metadata")

    class Config:
        """Pydantic config."""

        extra = "allow"
