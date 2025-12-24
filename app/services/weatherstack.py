"""Weatherstack API client service."""

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
    """Service for interacting with Weatherstack API."""

    def __init__(self):
        self.base_url = settings.WEATHERSTACK_BASE_URL
        self.api_key = settings.WEATHERSTACK_API_KEY
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_current_weather(self, city: str) -> Dict[str, Any]:
        """
        Fetch current weather for a city from Weatherstack API.

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
        url = f"{self.base_url}/current"
        params = {
            "access_key": self.api_key,
            "query": city,
        }

        try:
            logger.info(f"Fetching weather for city: {city}")
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
                logger.error(f"HTTP error {status_code}: {e}")
                raise WeatherstackAPIError(f"HTTP error {status_code}")

        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise WeatherstackAPIError(f"Failed to connect to Weatherstack API: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise WeatherstackAPIError(f"Unexpected error: {str(e)}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global service instance
weatherstack_service = WeatherstackService()

