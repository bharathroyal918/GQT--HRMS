"""Development settings for GQT HRMS platform."""
from .base import *  # noqa: F403
from .base import env, BASE_DIR

DEBUG = True
ENVIRONMENT = "development"

# Fallback to dev_local.sqlite3 only when USE_SQLITE_FOR_LOCAL_DEV is explicitly True
# or when neither DATABASE_URL nor DB_HOST is configured.
if env.bool("USE_SQLITE_FOR_LOCAL_DEV", default=False) or (
    not env.str("DATABASE_URL", default="") and not env.str("DB_HOST", default="")
):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "dev_local.sqlite3",
        }
    }
