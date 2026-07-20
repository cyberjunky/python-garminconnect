class GarminConnectConnectionError(Exception):
    """Raised when communication ended in error."""


class GarminConnectNotFoundError(GarminConnectConnectionError):
    """Raised when a requested resource does not exist (HTTP 404).

    Subclasses GarminConnectConnectionError for backwards compatibility, so
    existing ``except GarminConnectConnectionError`` handlers keep working while
    callers can now catch a missing resource specifically (e.g. deleting an
    already-deleted workout).
    """


class GarminConnectTooManyRequestsError(Exception):
    """Raised when rate limit is exceeded."""


class GarminConnectAuthenticationError(Exception):
    """Raised when authentication is failed."""


class GarminConnectInvalidFileFormatError(Exception):
    """Raised when an invalid file format is provided."""
