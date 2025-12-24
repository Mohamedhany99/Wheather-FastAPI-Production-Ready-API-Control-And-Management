"""Shared dependencies for dependency injection."""

import logging
from functools import lru_cache
from typing import Dict, Any

from cachetools import TTLCache

from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """In-memory cache manager using TTLCache."""

    def __init__(self, ttl_seconds: int):
        self.cache: TTLCache[str, Dict[str, Any]] = TTLCache(
            maxsize=1000, ttl=ttl_seconds
        )

    def get(self, key: str) -> Dict[str, Any] | None:
        """Get value from cache."""
        value = self.cache.get(key)
        if value:
            logger.debug(f"Cache hit for key: {key}")
        else:
            logger.debug(f"Cache miss for key: {key}")
        return value

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set value in cache."""
        self.cache[key] = value
        logger.debug(f"Cached value for key: {key}")

    def generate_key(self, city: str) -> str:
        """Generate cache key for a city."""
        return f"weather:{city.lower().strip()}"


@lru_cache()
def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance."""
    return CacheManager(ttl_seconds=settings.CACHE_TTL_SECONDS)

