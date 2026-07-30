class ClickyAPIError(Exception):
    """Raised when the Clicky API reports an error."""


class AuthenticationError(ClickyAPIError):
    """Raised when auth is missing/invalid/expired (401)."""


class InvalidEndpoint(ClickyAPIError):
    """Raised when an invalid endpoint is accessed (404)."""


class ConnectionError(ClickyAPIError):
    """Raised when the client can't reach the server (network failures)."""


class ServiceUnavailable(ClickyAPIError):
    """Raised when the service is temporarily down (503)."""
