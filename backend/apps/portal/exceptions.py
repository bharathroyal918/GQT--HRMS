"""Exceptions for Student Portal Integration Gateway."""


class PortalIntegrationError(Exception):
    """Base exception for all portal communication failures."""
    pass


class PortalDisabledError(PortalIntegrationError):
    """Raised when an operation is attempted while portal integration is disabled."""
    pass


class PortalConnectionError(PortalIntegrationError):
    """Raised when network connection to the Student Portal fails."""
    pass


class PortalTimeoutError(PortalIntegrationError):
    """Raised when a request to the Student Portal times out."""
    pass


class PortalAuthError(PortalIntegrationError):
    """Raised when authentication with the Student Portal is rejected."""
    pass


class PortalAPIError(PortalIntegrationError):
    """Raised when the Student Portal returns a non-2xx HTTP status."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(f"Portal API returned status {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail
