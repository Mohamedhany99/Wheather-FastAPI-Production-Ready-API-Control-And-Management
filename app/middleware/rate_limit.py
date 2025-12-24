"""Rate limiting middleware using slowapi."""

import logging

from fastapi import Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


def get_rate_limiter() -> Limiter:
    """Get the rate limiter instance."""
    return limiter


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded."""
    logger.warning(
        f"Rate limit exceeded for IP: {get_remote_address(request)}"
    )
    return _rate_limit_exceeded_handler(request, exc)

