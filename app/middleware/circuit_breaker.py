"""Circuit breaker pattern implementation for resilience."""

import logging
import time
from enum import Enum
from typing import Callable, Any
from dataclasses import dataclass, field

from app.config import settings

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, fast-fail
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    failures: int = 0
    successes: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    state_changes: int = 0


class CircuitBreaker:
    """Circuit breaker implementation to prevent cascading failures."""

    def __init__(
        self,
        failure_threshold: int = None,
        recovery_timeout: int = None,
        failure_rate_threshold: float = None,
    ):
        self.failure_threshold = (
            failure_threshold or settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        )
        self.recovery_timeout = (
            recovery_timeout or settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        )
        self.failure_rate_threshold = (
            failure_rate_threshold or settings.CIRCUIT_BREAKER_FAILURE_RATE_THRESHOLD
        )

        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.opened_at: float | None = None
        self._recent_requests: list[bool] = []  # True = success, False = failure
        self._max_recent_requests = 20  # Track last 20 requests for failure rate

    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self.state == CircuitState.OPEN

    def is_closed(self) -> bool:
        """Check if circuit breaker is closed."""
        return self.state == CircuitState.CLOSED

    def is_half_open(self) -> bool:
        """Check if circuit breaker is half-open."""
        return self.state == CircuitState.HALF_OPEN

    def _should_attempt_request(self) -> bool:
        """Determine if request should be attempted based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.opened_at and (time.time() - self.opened_at) >= self.recovery_timeout:
                logger.info("Circuit breaker transitioning to HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
                self.stats.state_changes += 1
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def _record_success(self):
        """Record a successful request."""
        self.stats.successes += 1
        self.stats.last_success_time = time.time()
        self._recent_requests.append(True)
        if len(self._recent_requests) > self._max_recent_requests:
            self._recent_requests.pop(0)

        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker transitioning to CLOSED state (recovered)")
            self.state = CircuitState.CLOSED
            self.stats.state_changes += 1
            self.opened_at = None
            self.stats.failures = 0

    def _record_failure(self):
        """Record a failed request."""
        self.stats.failures += 1
        self.stats.last_failure_time = time.time()
        self._recent_requests.append(False)
        if len(self._recent_requests) > self._max_recent_requests:
            self._recent_requests.pop(0)

        # Check if we should open the circuit
        if self.state == CircuitState.CLOSED:
            failure_rate = self._calculate_failure_rate()
            if (
                self.stats.failures >= self.failure_threshold
                or failure_rate >= self.failure_rate_threshold
            ):
                logger.warning(
                    f"Circuit breaker opening: {self.stats.failures} failures, "
                    f"failure rate: {failure_rate:.2%}"
                )
                self.state = CircuitState.OPEN
                self.stats.state_changes += 1
                self.opened_at = time.time()
                # Track circuit breaker opening in metrics
                try:
                    from app.middleware.metrics import get_metrics
                    get_metrics().record_circuit_breaker_open()
                except ImportError:
                    pass  # Metrics not available

        elif self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker reopening after failed recovery attempt")
            self.state = CircuitState.OPEN
            self.stats.state_changes += 1
            self.opened_at = time.time()

    def _calculate_failure_rate(self) -> float:
        """Calculate failure rate from recent requests."""
        if not self._recent_requests:
            return 0.0
        failures = sum(1 for r in self._recent_requests if not r)
        return failures / len(self._recent_requests)

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception from func if it fails
        """
        if not self._should_attempt_request():
            from app.exceptions import CircuitBreakerOpenError

            raise CircuitBreakerOpenError(
                "Circuit breaker is OPEN. Service unavailable."
            )

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise

    def get_state(self) -> dict:
        """Get current circuit breaker state and statistics."""
        return {
            "state": self.state.value,
            "failures": self.stats.failures,
            "successes": self.stats.successes,
            "failure_rate": self._calculate_failure_rate(),
            "opened_at": self.opened_at,
            "state_changes": self.stats.state_changes,
        }


# Global circuit breaker instance
circuit_breaker = CircuitBreaker()


def get_circuit_breaker() -> CircuitBreaker:
    """Get the global circuit breaker instance."""
    return circuit_breaker

