"""Automated test settings for GQT HRMS platform.

Optimized for:
- 100% Isolated in-memory/test SQLite execution
- Disposable temporary directory for MEDIA_ROOT (zero pollution of workspace)
- Fast password hashing (MD5 instead of Argon2id)
- Zero external network dependencies
"""
import os
import tempfile
from pathlib import Path
from .base import *  # noqa: F403

DEBUG = False
ENVIRONMENT = "testing"

SECRET_KEY = "django-insecure-test-environment-isolated-secret-key-for-pytest-runs"
ALLOWED_HOSTS = ["*"]

# Database Configuration: SQLite in-memory by default, or PostgreSQL 16 when POSTGRES_TEST_DATABASE_URL is provided
postgres_test_url = os.environ.get("POSTGRES_TEST_DATABASE_URL")
if postgres_test_url:
    parsed_db = env.db_url_config(postgres_test_url)
    parsed_db.setdefault("OPTIONS", {})
    if os.environ.get("DB_SSLMODE"):
        parsed_db["OPTIONS"]["sslmode"] = os.environ["DB_SSLMODE"]
    DATABASES = {"default": parsed_db}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# Temporary isolated media root for testing — eliminates test file pollution
TEST_TEMP_MEDIA = Path(tempfile.gettempdir()) / "gqt_hrms_isolated_test_media"
TEST_TEMP_MEDIA.mkdir(parents=True, exist_ok=True)
MEDIA_ROOT = TEST_TEMP_MEDIA
PRIVATE_MEDIA_ROOT = TEST_TEMP_MEDIA / "private"
PRIVATE_MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# Use fast hasher for automated unit/integration tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable throttles in automated test runs
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
