"""Weatherstack API client service with retry logic."""

import asyncio
import logging
from typing import Dict, Any

import httpx

from app.config import settings
from app.exceptions import (
    WeatherstackAPIError,
    WeatherstackAuthError,
    WeatherstackNotFoundError,
    WeatherstackRateLimitError,
)

logger = logging.getLogger(__name__)


class WeatherstackService:
    """Service for interacting with Weatherstack API with retry logic."""

    def __init__(self):
        self.base_url = settings.WEATHERSTACK_BASE_URL
        self.api_key = settings.WEATHERSTACK_API_KEY
        # Enhanced timeout configuration
        timeout = httpx.Timeout(
            connect=settings.HTTP_CONNECT_TIMEOUT,
            read=settings.HTTP_READ_TIMEOUT,
            write=5.0,
            pool=5.0,
        )
        self.client = httpx.AsyncClient(timeout=timeout)

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable."""
        # Don't retry on client errors (4xx)
        if isinstance(error, WeatherstackAuthError):
            return False
        if isinstance(error, WeatherstackNotFoundError):
            return False
        if isinstance(error, WeatherstackRateLimitError):
            return False

        # Retry on network errors and server errors
        if isinstance(error, httpx.TimeoutException):
            return True
        if isinstance(error, httpx.ConnectError):
            return True
        if isinstance(error, httpx.RequestError):
            return True
        if isinstance(error, WeatherstackAPIError):
            return True

        return False

    async def _fetch_weather_once(self, city: str) -> Dict[str, Any]:
        """Fetch weather data with a single attempt."""
        url = f"{self.base_url}/current"
        params = {
            "access_key": self.api_key,
            "query": city,
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Check for Weatherstack API errors in response
        if "error" in data:
            error_info = data.get("error", {})
            error_code = error_info.get("code")
            error_message = error_info.get("info", "Unknown error")

            if error_code == 404:
                logger.warning(f"City not found: {city}")
                raise WeatherstackNotFoundError(f"City '{city}' not found")
            elif error_code == 401:
                logger.error("Invalid API key")
                raise WeatherstackAuthError("Invalid API key")
            elif error_code == 429:
                logger.warning("Rate limit exceeded")
                raise WeatherstackRateLimitError("Rate limit exceeded")
            else:
                logger.error(f"Weatherstack API error: {error_message}")
                raise WeatherstackAPIError(f"Weatherstack API error: {error_message}")

        return data

    async def get_current_weather(self, city: str) -> Dict[str, Any]:
        """
        Fetch current weather for a city from Weatherstack API with retry logic.

        Args:
            city: Name of the city to get weather for

        Returns:
            Raw Weatherstack API response as dictionary

        Raises:
            WeatherstackAuthError: If API key is invalid
            WeatherstackNotFoundError: If city is not found
            WeatherstackRateLimitError: If rate limit is exceeded
            WeatherstackAPIError: For other API errors
        """
        max_attempts = settings.RETRY_MAX_ATTEMPTS
        backoff_base = settings.RETRY_BACKOFF_BASE

        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                if attempt > 1:
                    wait_time = backoff_base * (2 ** (attempt - 2))
                    logger.info(
                        f"Retry attempt {attempt}/{max_attempts} for city {city} "
                        f"after {wait_time:.1f}s"
                    )
                    await asyncio.sleep(wait_time)

                logger.info(f"Fetching weather for city: {city} (attempt {attempt}/{max_attempts})")
                data = await self._fetch_weather_once(city)
                logger.info(f"Successfully fetched weather for {city}")
                return data

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                if status_code == 401:
                    logger.error("Authentication failed")
                    raise WeatherstackAuthError("Invalid API key")
                elif status_code == 404:
                    logger.warning(f"City not found: {city}")
                    raise WeatherstackNotFoundError(f"City '{city}' not found")
                elif status_code == 429:
                    logger.warning("Rate limit exceeded")
                    raise WeatherstackRateLimitError("Rate limit exceeded")
                else:
                    last_error = WeatherstackAPIError(f"HTTP error {status_code}")
                    if not self._is_retryable_error(last_error):
                        raise last_error

            except httpx.TimeoutException as e:
                last_error = WeatherstackAPIError(f"Request timeout: {str(e)}")
                logger.warning(f"Timeout on attempt {attempt}: {e}")

            except httpx.ConnectError as e:
                last_error = WeatherstackAPIError(f"Connection error: {str(e)}")
                logger.warning(f"Connection error on attempt {attempt}: {e}")

            except httpx.RequestError as e:
                last_error = WeatherstackAPIError(f"Request error: {str(e)}")
                logger.warning(f"Request error on attempt {attempt}: {e}")

            except WeatherstackAPIError as e:
                # Don't retry on non-retryable errors
                if not self._is_retryable_error(e):
                    raise
                last_error = e

            except Exception as e:
                last_error = WeatherstackAPIError(f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error on attempt {attempt}: {e}")

        # All retries exhausted
        logger.error(
            f"Failed to fetch weather for {city} after {max_attempts} attempts. "
            f"Last error: {last_error}"
        )
        if last_error:
            raise last_error
        raise WeatherstackAPIError("Failed to fetch weather data after retries")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global service instance
weatherstack_service = WeatherstackService()
