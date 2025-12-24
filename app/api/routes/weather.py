"""Weather API endpoint with resilience features."""

import logging
import time
from typing import Dict, Any

from fastapi import APIRouter, Query, HTTPException, Depends, Request
from slowapi import Limiter

from app.services.weatherstack import weatherstack_service
from app.dependencies import get_cache_manager, CacheManager
from app.middleware.rate_limit import get_rate_limiter
from app.middleware.circuit_breaker import get_circuit_breaker, CircuitBreaker
from app.middleware.metrics import get_metrics
from app.exceptions import WeatherstackException, CircuitBreakerOpenError
from app.models.response import ResponseMetadata

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["weather"])
limiter = get_rate_limiter()
metrics = get_metrics()


def _build_response(
    data: Dict[str, Any], metadata: Dict[str, Any], circuit_breaker: CircuitBreaker
) -> Dict[str, Any]:
    """Build response with data and metadata."""
    cb_state = circuit_breaker.get_state()
    metadata["circuit_breaker_state"] = cb_state["state"]

    response = {
        "data": data,
        "metadata": metadata,
    }
    return response


@router.get("")
@limiter.limit("60/minute")
async def get_weather(
    request: Request,
    city: str = Query(..., description="Name of the city to get weather for"),
    cache: CacheManager = Depends(get_cache_manager),
    circuit_breaker: CircuitBreaker = Depends(get_circuit_breaker),
) -> Dict[str, Any]:
    """
    Get current weather for a city with resilience features.

    This endpoint fetches current weather data from Weatherstack API for the specified city.
    Features:
    - Caching with stale cache fallback
    - Circuit breaker pattern
    - Retry logic with exponential backoff
    - Enhanced error handling

    Args:
        city: Name of the city
        request: FastAPI request object (used by rate limiter)
        cache: Cache manager dependency
        circuit_breaker: Circuit breaker dependency

    Returns:
        Dictionary with 'data' (weather data) and 'metadata' (response metadata)

    Raises:
        HTTPException: With appropriate status code for various error scenarios
    """
    if not city or not city.strip():
        logger.warning("Empty city parameter provided")
        raise HTTPException(status_code=400, detail="City parameter is required")

    city = city.strip()
    cache_key = cache.generate_key(city)
    start_time = time.time()

    # Check fresh cache first
    cached_response = cache.get(cache_key)
    if cached_response:
        logger.info(f"Returning fresh cached weather data for {city}")
        metrics.record_cache_hit()
        duration = time.time() - start_time
        metrics.record_response_time(duration)
        _, metadata = cache.get_with_metadata(cache_key)
        return _build_response(cached_response, metadata, circuit_breaker)

    metrics.record_cache_miss()

    # Try to fetch from Weatherstack API with circuit breaker protection
    try:
        logger.info(f"Fetching weather data for city: {city}")
        metrics.record_request()
        weather_data = await circuit_breaker.call(
            weatherstack_service.get_current_weather, city
        )

        # Store in cache
        cache.set(cache_key, weather_data)
        logger.info(f"Successfully fetched and cached weather data for {city}")

        duration = time.time() - start_time
        metrics.record_response_time(duration)

        metadata = {
            "cached": False,
            "stale": False,
            "age_seconds": 0,
            "source": "api",
            "retry_attempts": 0,
        }
        return _build_response(weather_data, metadata, circuit_breaker)

    except CircuitBreakerOpenError:
        # Circuit breaker is open - try stale cache fallback
        logger.warning(f"Circuit breaker is OPEN for {city}, attempting stale cache fallback")
        metrics.record_error("circuit_breaker_open")
        stale_data, stale_metadata = cache.get_stale(cache_key)

        if stale_data:
            logger.info(f"Returning stale cache for {city} due to circuit breaker being open")
            metrics.record_stale_cache_fallback()
            duration = time.time() - start_time
            metrics.record_response_time(duration)
            return _build_response(stale_data, stale_metadata, circuit_breaker)
        else:
            logger.error(f"No stale cache available for {city}, circuit breaker is open")
            duration = time.time() - start_time
            metrics.record_response_time(duration)
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable. Please try again later.",
            )

    except WeatherstackException as e:
        # Weatherstack error - try stale cache fallback
        logger.warning(
            f"Weatherstack error for city {city}: {e.message}, attempting stale cache fallback"
        )
        metrics.record_error(type(e).__name__)
        stale_data, stale_metadata = cache.get_stale(cache_key)

        if stale_data:
            logger.info(f"Returning stale cache for {city} due to API error")
            metrics.record_stale_cache_fallback()
            duration = time.time() - start_time
            metrics.record_response_time(duration)
            return _build_response(stale_data, stale_metadata, circuit_breaker)
        else:
            # No stale cache available, return error
            logger.error(f"Weatherstack error for city {city}: {e.message}")
            duration = time.time() - start_time
            metrics.record_response_time(duration)
            raise HTTPException(status_code=e.status_code, detail=e.message)

    except Exception as e:
        # Unexpected error - try stale cache fallback
        logger.error(f"Unexpected error fetching weather for {city}: {e}")
        metrics.record_error("unexpected_error")
        stale_data, stale_metadata = cache.get_stale(cache_key)

        if stale_data:
            logger.info(f"Returning stale cache for {city} due to unexpected error")
            metrics.record_stale_cache_fallback()
            duration = time.time() - start_time
            metrics.record_response_time(duration)
            return _build_response(stale_data, stale_metadata, circuit_breaker)
        else:
            logger.error(f"Unexpected error and no stale cache for {city}: {e}")
            duration = time.time() - start_time
            metrics.record_response_time(duration)
            raise HTTPException(status_code=500, detail="Internal server error")

