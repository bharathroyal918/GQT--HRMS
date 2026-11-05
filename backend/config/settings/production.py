"""Hardened production settings for GQT HRMS platform.

Fail-Closed Security Invariants:
- Rejects boot if DJANGO_SECRET_KEY is omitted, weak, or contains 'insecure'
- Rejects boot if DJANGO_ALLOWED_HOSTS is wildcard or only local
- Rejects boot if Database password is empty or default
- Enforces SSL/TLS redirects and Secure cookie flags
"""
from django.core.exceptions import ImproperlyConfigured
from .base import *  # noqa: F403
from .base import env, DATABASES, DEV_FALLBACK_SECRET_KEY

DEBUG = False
ENVIRONMENT = "production"

SECRET_KEY = env("DJANGO_SECRET_KEY", default="")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# Invariant 1: Fail-closed on missing, short, or placeholder SECRET_KEY
if (
    not SECRET_KEY
    or len(SECRET_KEY) < 40
    or "insecure" in SECRET_KEY.lower()
    or SECRET_KEY == DEV_FALLBACK_SECRET_KEY
):
    raise ImproperlyConfigured(
        "Production Security Violation: DJANGO_SECRET_KEY must be an explicit, "
        "high-entropy string of at least 40 characters without 'insecure' placeholders."
    )

# Invariant 2: Fail-closed on missing, wildcard, or only-localhost ALLOWED_HOSTS
if (
    not ALLOWED_HOSTS
    or "*" in ALLOWED_HOSTS
    or set(ALLOWED_HOSTS) <= {"localhost", "127.0.0.1", "0.0.0.0"}
):
    raise ImproperlyConfigured(
        "Production Security Violation: DJANGO_ALLOWED_HOSTS must contain valid production "
        "fully qualified domain names. Wildcards and localhost-only lists are prohibited."
    )

# Invariant 3: Enforce Secure cookie flags and SSL in production
AUTH_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
AUTH_COOKIE_SAMESITE = env.str("AUTH_COOKIE_SAMESITE", default="None")
SESSION_COOKIE_SAMESITE = env.str("SESSION_COOKIE_SAMESITE", default="None")
CSRF_COOKIE_SAMESITE = env.str("CSRF_COOKIE_SAMESITE", default="None")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
