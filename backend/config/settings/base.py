"""Base Django settings for GQT HRMS & Recruitment CRM Platform.

Architectural Standards:
- Enterprise Modular 5-Layer Pattern
- PostgreSQL 16 Support via psycopg v3 with SSL
- Strict Secret Redaction & Audit Logging
- OpenAPI 3.1 Documentation via drf-spectacular
- Deny-by-default Authorization
"""
from pathlib import Path
import os
from datetime import timedelta
import environ

# Paths: BASE_DIR is backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BASE_DIR.parent

env = environ.Env(
    ENVIRONMENT=(str, "development"),
    DEBUG=(bool, False),
    TIMEZONE=(str, "Asia/Kolkata"),
    LOG_LEVEL=(str, "INFO"),
    USE_SQLITE_FOR_LOCAL_DEV=(bool, True),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173", "http://127.0.0.1:5173"]),
    CSRF_TRUSTED_ORIGINS=(list, ["http://localhost:5173", "http://127.0.0.1:5173"]),
    SESSION_COOKIE_SECURE=(bool, False),
    CSRF_COOKIE_SECURE=(bool, False),
    JWT_COOKIE_SECURE=(bool, False),
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 15),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
    MEDIA_ROOT=(str, ""),
    PRIVATE_MEDIA_ROOT=(str, ""),
    STUDENT_PORTAL_BASE_URL=(str, "http://127.0.0.1:8001/api/v1"),
    STUDENT_PORTAL_HR_EMAIL=(str, "hrms-service@gqt.local"),
    STUDENT_PORTAL_API_KEY=(str, "mock-portal-service-token-disabled-in-dev"),
    STUDENT_PORTAL_WEB_URL=(str, "http://127.0.0.1:3000"),
    STUDENT_PORTAL_ENABLED=(bool, False),
)

# Load .env file from either backend/ or repo root
skip_dotenv = os.environ.get("SKIP_DOTENV", "").lower() in ("true", "1", "yes")
if not skip_dotenv:
    if (BASE_DIR / ".env").exists():
        environ.Env.read_env(str(BASE_DIR / ".env"))
    elif (REPO_ROOT / ".env").exists():
        environ.Env.read_env(str(REPO_ROOT / ".env"))

ENVIRONMENT = env("ENVIRONMENT")
DEBUG = env("DEBUG")

DEV_FALLBACK_SECRET_KEY = (
    "django-insecure-dev-only-secret-key-must-be-rotated-for-production-min-50-chars"
)

if ENVIRONMENT == "production":
    SECRET_KEY = env("DJANGO_SECRET_KEY", default="")
else:
    SECRET_KEY = env("DJANGO_SECRET_KEY", default=DEV_FALLBACK_SECRET_KEY)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.core.apps.CoreConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.portal.apps.PortalConfig",
    "apps.crm.apps.CrmConfig",
    "apps.jobs.apps.JobsConfig",
    "apps.creatives.apps.CreativesConfig",
    "apps.students.apps.StudentsConfig",
    "apps.preparation.apps.PreparationConfig",
    "apps.submissions.apps.SubmissionsConfig",
    "apps.interviews.apps.InterviewsConfig",
    "apps.placements.apps.PlacementsConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "apps.core.middleware.CorrelationIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database Configuration (PostgreSQL 16 as primary, SQLite fallback for offline dev)
DATABASE_URL = env.str("DATABASE_URL", default="")
DB_HOST = env.str("DB_HOST", default="")
USE_SQLITE = env.bool("USE_SQLITE_FOR_LOCAL_DEV", default=False)

if DATABASE_URL and not USE_SQLITE:
    DATABASES = {
        "default": env.db_url("DATABASE_URL", engine="django.db.backends.postgresql")
    }
    DATABASES["default"].setdefault("OPTIONS", {})["sslmode"] = env.str("DB_SSLMODE", default="require")
elif DB_HOST and not USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env.str("DB_NAME", default="postgres"),
            "USER": env.str("DB_USER", default="postgres"),
            "PASSWORD": env.str("DB_PASSWORD", default=""),
            "HOST": DB_HOST,
            "PORT": env.str("DB_PORT", default="5432"),
            "OPTIONS": {
                "sslmode": env.str("DB_SSLMODE", default="require"),
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "dev_local.sqlite3",
        }
    }

if DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"]["sslmode"] = env.str("DB_SSLMODE", default="require")
    DATABASES["default"]["OPTIONS"]["connect_timeout"] = env.int("DB_CONNECT_TIMEOUT", default=10)
    is_pooler = "pooler" in DATABASES["default"].get("HOST", "") or str(
        DATABASES["default"].get("PORT", "")
    ) in ("6543", "6432")
    if is_pooler or env.bool("DB_DISABLE_PREPARED_STATEMENTS", default=False):
        DATABASES["default"]["OPTIONS"]["prepare_threshold"] = None
    DATABASES["default"]["CONN_MAX_AGE"] = env.int(
        "DB_CONN_MAX_AGE", default=0 if is_pooler else 60
    )

# Password Hashing — Argon2id by default for high security
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIMEZONE", default="Asia/Kolkata")
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media files (Resumes, Creatives, Offer Letters)
configured_media_root = env.str("MEDIA_ROOT", default="")
if configured_media_root and configured_media_root.strip():
    MEDIA_ROOT = Path(configured_media_root)
else:
    MEDIA_ROOT = BASE_DIR / "media"

configured_private_media_root = env.str("PRIVATE_MEDIA_ROOT", default="")
if configured_private_media_root and configured_private_media_root.strip():
    PRIVATE_MEDIA_ROOT = Path(configured_private_media_root)
else:
    PRIVATE_MEDIA_ROOT = MEDIA_ROOT / "private"

MEDIA_URL = "/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework Settings — Deny by default
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.accounts.authentication.JWTCookieAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "auth_login": "5/minute",
    },
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}

# SimpleJWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=15)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SIGNING_KEY", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# Cookie Settings for Authentication
AUTH_COOKIE_ACCESS = "gqt_access_token"
AUTH_COOKIE_REFRESH = "gqt_refresh_token"
AUTH_COOKIE_SECURE = env.bool("JWT_COOKIE_SECURE", default=False)
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_SAMESITE = env.str("AUTH_COOKIE_SAMESITE", default="Lax")

# CORS & CSRF
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)

SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
SESSION_COOKIE_SAMESITE = env.str("SESSION_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
CSRF_COOKIE_SAMESITE = env.str("CSRF_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_HTTPONLY = False

# drf-spectacular OpenAPI 3.1
SPECTACULAR_SETTINGS = {
    "TITLE": "GQT HRMS & Recruitment CRM Platform API",
    "DESCRIPTION": (
        "Production REST API for recruitment CRM, job verification, "
        "student eligibility, interviews, placements, and Student Portal integration."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v1/",
    "COMPONENT_SPLIT_REQUEST": True,
}

# Logging configuration with sensitive data redaction
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "sensitive_data": {
            "()": "apps.core.logging.SensitiveDataFilter",
        },
    },
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] [%(levelname)s] [req:%(correlation_id)s] [%(name)s]: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "filters": ["sensitive_data"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env.str("LOG_LEVEL", default="INFO"),
    },
}

# Student Portal Integration Settings
STUDENT_PORTAL_BASE_URL = env.str(
    "STUDENT_PORTAL_BASE_URL", default="http://127.0.0.1:8001/api/v1"
)
STUDENT_PORTAL_HR_EMAIL = env.str(
    "STUDENT_PORTAL_HR_EMAIL", default="hrms-service@gqt.local"
)
STUDENT_PORTAL_API_KEY = env.str(
    "STUDENT_PORTAL_API_KEY", default="mock-portal-service-token-disabled-in-dev"
)
STUDENT_PORTAL_WEB_URL = env.str(
    "STUDENT_PORTAL_WEB_URL", default="http://127.0.0.1:3000"
)
STUDENT_PORTAL_ENABLED = env.bool("STUDENT_PORTAL_ENABLED", default=False)

