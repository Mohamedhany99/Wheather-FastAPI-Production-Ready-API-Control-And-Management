"""Metrics collection for observability."""

import logging
import time
from typing import Dict, Any
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Metrics:
    """Simple in-memory metrics collector (ready for Prometheus/DataDog integration)."""

    # Counters
    api_requests_total: int = 0
    api_errors_total: int = 0
    api_timeouts_total: int = 0
    cache_hits_total: int = 0
    cache_misses_total: int = 0
    stale_cache_fallbacks_total: int = 0
    circuit_breaker_opens_total: int = 0
    retry_attempts_total: int = 0

    # Error counters by type
    errors_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Response time tracking
    response_times: list[float] = field(default_factory=list)
    max_response_times: int = 1000  # Keep last 1000 response times

    def record_request(self):
        """Record an API request."""
        self.api_requests_total += 1

    def record_error(self, error_type: str = "unknown"):
        """Record an API error."""
        self.api_errors_total += 1
        self.errors_by_type[error_type] += 1

    def record_timeout(self):
        """Record a timeout."""
        self.api_timeouts_total += 1
        self.record_error("timeout")

    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_hits_total += 1

    def record_cache_miss(self):
        """Record a cache miss."""
        self.cache_misses_total += 1

    def record_stale_cache_fallback(self):
        """Record a stale cache fallback."""
        self.stale_cache_fallbacks_total += 1

    def record_circuit_breaker_open(self):
        """Record circuit breaker opening."""
        self.circuit_breaker_opens_total += 1

    def record_retry(self):
        """Record a retry attempt."""
        self.retry_attempts_total += 1

    def record_response_time(self, duration_seconds: float):
        """Record response time."""
        self.response_times.append(duration_seconds)
        if len(self.response_times) > self.max_response_times:
            self.response_times.pop(0)

    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits_total + self.cache_misses_total
        if total == 0:
            return 0.0
        return self.cache_hits_total / total

    def get_error_rate(self) -> float:
        """Calculate error rate."""
        if self.api_requests_total == 0:
            return 0.0
        return self.api_errors_total / self.api_requests_total

    def get_percentile(self, percentile: float) -> float:
        """Get percentile response time (e.g., 0.95 for p95)."""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * percentile)
        return sorted_times[min(index, len(sorted_times) - 1)]

    def get_stats(self) -> Dict[str, Any]:
        """Get all metrics as dictionary."""
        return {
            "counters": {
                "api_requests_total": self.api_requests_total,
                "api_errors_total": self.api_errors_total,
                "api_timeouts_total": self.api_timeouts_total,
                "cache_hits_total": self.cache_hits_total,
                "cache_misses_total": self.cache_misses_total,
                "stale_cache_fallbacks_total": self.stale_cache_fallbacks_total,
                "circuit_breaker_opens_total": self.circuit_breaker_opens_total,
                "retry_attempts_total": self.retry_attempts_total,
            },
            "errors_by_type": dict(self.errors_by_type),
            "rates": {
                "cache_hit_rate": self.get_cache_hit_rate(),
                "error_rate": self.get_error_rate(),
            },
            "response_times": {
                "p50": self.get_percentile(0.50),
                "p95": self.get_percentile(0.95),
                "p99": self.get_percentile(0.99),
                "count": len(self.response_times),
            },
        }

    def log_summary(self):
        """Log metrics summary."""
        stats = self.get_stats()
        logger.info("Metrics Summary:")
        logger.info(f"  Requests: {stats['counters']['api_requests_total']}")
        logger.info(f"  Errors: {stats['counters']['api_errors_total']}")
        logger.info(f"  Cache Hit Rate: {stats['rates']['cache_hit_rate']:.2%}")
        logger.info(f"  Error Rate: {stats['rates']['error_rate']:.2%}")
        logger.info(f"  P95 Response Time: {stats['response_times']['p95']:.3f}s")


# Global metrics instance
metrics = Metrics()


def get_metrics() -> Metrics:
    """Get the global metrics instance."""
    return metrics


class MetricsMiddleware:
    """Middleware for tracking request metrics."""

    def __init__(self, metrics_instance: Metrics = None):
        self.metrics = metrics_instance or metrics

    async def track_request(self, func, *args, **kwargs):
        """Track a request with timing."""
        start_time = time.time()
        self.metrics.record_request()

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            self.metrics.record_response_time(duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.metrics.record_response_time(duration)
            error_type = type(e).__name__
            self.metrics.record_error(error_type)
            raise

