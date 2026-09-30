"""Exceptions raised by the Daikin Onecta client."""


class OnectaError(Exception):
    """Base exception for Daikin Onecta errors."""


class OnectaConnectionError(OnectaError):
    """Raised when communication with the Daikin Onecta API fails."""


class OnectaAuthenticationError(OnectaError):
    """Raised when authentication with the Daikin Onecta API fails."""


class OnectaRateLimitError(OnectaError):
    """Raised when the Daikin Onecta API rate limit is exceeded."""

    def __init__(self, retry_after: int | None, message: str = "Daikin Onecta API rate limit exceeded") -> None:
        """Initialize the rate limit error."""
        super().__init__(message)
        self.retry_after = retry_after


class OnectaApiError(OnectaError):
    """Raised when the Daikin Onecta API returns an unexpected response."""

    def __init__(self, status: int, message: str) -> None:
        """Initialize the API error."""
        super().__init__(f"Daikin Onecta API returned HTTP {status}: {message}")
        self.status = status
        self.message = message
