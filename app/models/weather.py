"""Pydantic models for Weatherstack API responses."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Location(BaseModel):
    """Location information from Weatherstack API."""

    name: str
    country: str
    region: Optional[str] = None
    lat: Optional[str] = None
    lon: Optional[str] = None
    timezone_id: Optional[str] = None
    localtime: Optional[str] = None
    localtime_epoch: Optional[int] = None
    utc_offset: Optional[str] = None


class Current(BaseModel):
    """Current weather conditions from Weatherstack API."""

    observation_time: Optional[str] = None
    temperature: int
    weather_code: int
    weather_icons: list[str] = Field(default_factory=list)
    weather_descriptions: list[str] = Field(default_factory=list)
    wind_speed: Optional[int] = None
    wind_degree: Optional[int] = None
    wind_dir: Optional[str] = None
    pressure: Optional[int] = None
    precip: Optional[float] = None
    humidity: Optional[int] = None
    cloudcover: Optional[int] = None
    feelslike: Optional[int] = None
    uv_index: Optional[int] = None
    visibility: Optional[int] = None
    is_day: Optional[str] = None


class WeatherstackResponse(BaseModel):
    """Complete Weatherstack API response model."""

    request: Optional[Dict[str, Any]] = None
    location: Optional[Location] = None
    current: Optional[Current] = None

    class Config:
        """Pydantic config."""

        extra = "allow"  # Allow extra fields from Weatherstack API

