"""Development settings for GQT HRMS platform."""
from .base import *  # noqa: F403
from .base import env, BASE_DIR

DEBUG = True
ENVIRONMENT = "development"

# When developing locally with SQLite, dev_local.sqlite3 is used if DATABASE_URL is not set
if not env.str("DATABASE_URL", default=""):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "dev_local.sqlite3",
        }
    }
