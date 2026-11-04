"""Rate limiting and throttling classes for sensitive authentication endpoints."""
from rest_framework.throttling import AnonRateThrottle


class AuthLoginRateThrottle(AnonRateThrottle):
    """Throttle restricting login attempts per IP address to 5 per minute."""

    scope = "auth_login"
