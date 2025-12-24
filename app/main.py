"""FastAPI application entry point."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api.routes import weather, health, metrics
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.exceptions import WeatherstackException, CircuitBreakerOpenError


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Weather API application")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Rate limit: {settings.RATE_LIMIT_PER_MINUTE} requests/minute")
    logger.info(f"Cache TTL: {settings.CACHE_TTL_SECONDS} seconds")
    logger.info(f"Stale cache max age: {settings.STALE_CACHE_MAX_AGE_SECONDS} seconds")
    logger.info(f"Retry max attempts: {settings.RETRY_MAX_ATTEMPTS}")
    logger.info(
        f"Circuit breaker: {settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD} failures, "
        f"{settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT}s recovery timeout"
    )
    yield
    # Shutdown
    logger.info("Shutting down Weather API application")
    from app.services.weatherstack import weatherstack_service
    await weatherstack_service.close()


# Create FastAPI application
app = FastAPI(
    title="Weather API",
    description="A FastAPI service for fetching weather data from Weatherstack API",
    version="0.1.0",
    lifespan=lifespan,
)

# Add rate limiting state to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Include routers
app.include_router(weather.router)
app.include_router(health.router)
app.include_router(metrics.router)


# Exception handlers
@app.exception_handler(WeatherstackException)
async def weatherstack_exception_handler(
    request: Request, exc: WeatherstackException
) -> JSONResponse:
    """Handle Weatherstack exceptions."""
    logger.error(f"Weatherstack exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": exc.__class__.__name__},
    )


@app.exception_handler(CircuitBreakerOpenError)
async def circuit_breaker_exception_handler(
    request: Request, exc: CircuitBreakerOpenError
) -> JSONResponse:
    """Handle circuit breaker open exceptions."""
    logger.warning(f"Circuit breaker open: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "error_type": exc.__class__.__name__},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Weather API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }

