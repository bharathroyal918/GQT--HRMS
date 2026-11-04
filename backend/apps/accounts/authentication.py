"""Custom JWT Authentication supporting HttpOnly cookies and Bearer headers."""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JWTCookieAuthentication(JWTAuthentication):
    """Authentication backend that extracts SimpleJWT tokens from HttpOnly cookies or Bearer headers."""

    def authenticate(self, request):
        # 1. Check HttpOnly cookie first
        cookie_name = getattr(settings, "AUTH_COOKIE_ACCESS", "gqt_access_token")
        raw_token = request.COOKIES.get(cookie_name)

        # 2. Fall back to standard Authorization: Bearer <token> header
        if not raw_token:
            header = self.get_header(request)
            if header is not None:
                raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except (InvalidToken, AuthenticationFailed):
            return None


class JWTCookieAuthenticationScheme(OpenApiAuthenticationExtension):
    """drf-spectacular OpenAPI security scheme registration for JWTCookieAuthentication."""

    target_class = "apps.accounts.authentication.JWTCookieAuthentication"
    name = "jwtCookieAuth"

    def get_security_requirement(self, auto_schema):
        return {self.name: []}

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": getattr(settings, "AUTH_COOKIE_ACCESS", "gqt_access_token"),
            "description": "HttpOnly JWT access token cookie set upon successful login.",
        }
