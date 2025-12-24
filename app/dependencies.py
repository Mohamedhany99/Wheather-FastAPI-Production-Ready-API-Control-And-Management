"""Shared dependencies for dependency injection."""

import logging
import time
from functools import lru_cache
from typing import Dict, Any, Tuple


from app.config import settings

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with timestamp for stale cache detection."""

    def __init__(self, data: Dict[str, Any], timestamp: float = None):
        self.data = data
        self.timestamp = timestamp or time.time()

    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.timestamp

    def is_stale(self, max_age_seconds: int) -> bool:
        """Check if cache entry is stale."""
        return self.age_seconds() > max_age_seconds


class CacheManager:
    """In-memory cache manager with stale cache support."""

    def __init__(self, ttl_seconds: int, stale_max_age_seconds: int = None):
        # Use regular dict to track entries with timestamps for stale cache support
        self._cache: Dict[str, CacheEntry] = {}
        self.ttl_seconds = ttl_seconds
        self.stale_max_age_seconds = stale_max_age_seconds or settings.STALE_CACHE_MAX_AGE_SECONDS
        self.maxsize = 1000

    def _cleanup_expired(self):
        """Remove entries that exceed stale max age."""
        keys_to_remove = []
        for key, entry in self._cache.items():
            if entry.age_seconds() > self.stale_max_age_seconds:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self._cache[key]

    def _evict_if_needed(self):
        """Evict oldest entries if cache is full."""
        if len(self._cache) >= self.maxsize:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
            del self._cache[oldest_key]

    def get(self, key: str) -> Dict[str, Any] | None:
        """Get fresh value from cache (not stale)."""
        entry = self._cache.get(key)
        if entry:
            age = entry.age_seconds()
            if age <= self.ttl_seconds:
                logger.debug(f"Cache hit for key: {key}, age: {age:.1f}s")
                return entry.data
            else:
                logger.debug(f"Cache entry expired for key: {key}, age: {age:.1f}s")
        else:
            logger.debug(f"Cache miss for key: {key}")
        return None

    def get_with_metadata(self, key: str) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
        """
        Get cache entry with metadata about freshness.

        Returns:
            Tuple of (data, metadata) where metadata contains:
            - cached: bool
            - stale: bool
            - age_seconds: float
            - source: str
        """
        entry = self._cache.get(key)
        if entry:
            age = entry.age_seconds()
            is_stale = age > self.ttl_seconds
            is_available = age <= self.stale_max_age_seconds

            if is_available:
                logger.debug(
                    f"Cache entry found for key: {key}, age: {age:.1f}s, stale: {is_stale}"
                )
                metadata = {
                    "cached": True,
                    "stale": is_stale,
                    "age_seconds": round(age, 1),
                    "source": "cache_fallback" if is_stale else "cache",
                }
                return entry.data, metadata
            else:
                logger.debug(f"Cache entry too old for key: {key}, age: {age:.1f}s")
        else:
            logger.debug(f"Cache miss for key: {key}")

        return None, {
            "cached": False,
            "stale": False,
            "age_seconds": 0,
            "source": "none",
        }

    def get_stale(self, key: str) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
        """
        Get stale cache entry if available (for fallback during outages).

        Returns:
            Tuple of (data, metadata) or (None, metadata) if not available
        """
        entry = self._cache.get(key)
        if entry:
            age = entry.age_seconds()
            if age <= self.stale_max_age_seconds:
                is_stale = age > self.ttl_seconds
                logger.info(
                    f"Returning {'stale' if is_stale else 'fresh'} cache for key: {key}, age: {age:.1f}s"
                )
                metadata = {
                    "cached": True,
                    "stale": is_stale,
                    "age_seconds": round(age, 1),
                    "source": "cache_fallback" if is_stale else "cache",
                }
                return entry.data, metadata

        return None, {
            "cached": False,
            "stale": False,
            "age_seconds": 0,
            "source": "none",
        }

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set value in cache with current timestamp."""
        self._evict_if_needed()
        entry = CacheEntry(value)
        self._cache[key] = entry
        logger.debug(f"Cached value for key: {key}")
        # Periodic cleanup
        if len(self._cache) % 100 == 0:
            self._cleanup_expired()

    def generate_key(self, city: str) -> str:
        """Generate cache key for a city."""
        return f"weather:{city.lower().strip()}"


@lru_cache()
def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance."""
    return CacheManager(ttl_seconds=settings.CACHE_TTL_SECONDS)
