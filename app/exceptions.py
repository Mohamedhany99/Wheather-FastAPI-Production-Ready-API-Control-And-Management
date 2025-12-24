"""Custom exception classes for Weatherstack API errors."""


class WeatherstackException(Exception):
    """Base exception for all Weatherstack-related errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class WeatherstackAPIError(WeatherstackException):
    """Exception for general API failures (500s)."""

    def __init__(self, message: str = "Weatherstack API error"):
        super().__init__(message, status_code=500)


class WeatherstackNotFoundError(WeatherstackException):
    """Exception for city not found (404)."""

    def __init__(self, message: str = "City not found"):
        super().__init__(message, status_code=404)


class WeatherstackRateLimitError(WeatherstackException):
    """Exception for rate limit exceeded (429)."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class WeatherstackAuthError(WeatherstackException):
    """Exception for authentication errors (invalid API key, 401)."""

    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, status_code=401)

