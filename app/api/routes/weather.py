"""Weather API endpoint."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Query, HTTPException, Depends, Request
from slowapi import Limiter

from app.services.weatherstack import weatherstack_service
from app.dependencies import get_cache_manager, CacheManager
from app.middleware.rate_limit import get_rate_limiter
from app.exceptions import WeatherstackException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["weather"])
limiter = get_rate_limiter()


@router.get("")
@limiter.limit("60/minute")
async def get_weather(
    request: Request,
    city: str = Query(..., description="Name of the city to get weather for"),
    cache: CacheManager = Depends(get_cache_manager),
) -> Dict[str, Any]:
    """
    Get current weather for a city.

    This endpoint fetches current weather data from Weatherstack API for the specified city.
    Results are cached for 5 minutes (configurable) to reduce API calls.

    Args:
        city: Name of the city
        request: FastAPI request object (used by rate limiter)
        cache: Cache manager dependency

    Returns:
        Raw Weatherstack API response as dictionary

    Raises:
        HTTPException: With appropriate status code for various error scenarios
    """
    if not city or not city.strip():
        logger.warning("Empty city parameter provided")
        raise HTTPException(status_code=400, detail="City parameter is required")

    city = city.strip()
    cache_key = cache.generate_key(city)

    # Check cache first
    cached_response = cache.get(cache_key)
    if cached_response:
        logger.info(f"Returning cached weather data for {city}")
        return cached_response

    # Fetch from Weatherstack API
    try:
        logger.info(f"Fetching weather data for city: {city}")
        weather_data = await weatherstack_service.get_current_weather(city)

        # Store in cache
        cache.set(cache_key, weather_data)
        logger.info(f"Successfully fetched and cached weather data for {city}")

        return weather_data

    except WeatherstackException as e:
        logger.error(f"Weatherstack error for city {city}: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error fetching weather for {city}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

