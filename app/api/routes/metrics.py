"""Metrics endpoint for observability."""

from fastapi import APIRouter

from app.middleware.metrics import get_metrics as get_metrics_instance

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def get_metrics_endpoint():
    """
    Get application metrics.

    Returns metrics including:
    - Request/error counters
    - Cache hit/miss rates
    - Response time percentiles (p50, p95, p99)
    - Circuit breaker statistics
    - Error breakdown by type
    """
    metrics_instance = get_metrics_instance()
    return metrics_instance.get_stats()
