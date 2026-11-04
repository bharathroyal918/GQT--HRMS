"""Production Settings Fail-Closed Security Tests."""
import os
import pytest
from django.core.exceptions import ImproperlyConfigured


def test_production_settings_rejects_missing_secret_key(monkeypatch):
    """Verify production settings fails closed if secret key is missing or insecure placeholder."""
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.production")
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "hrms.gqt.com")

    with pytest.raises(ImproperlyConfigured):
        # Reload or import production settings
        import importlib
        from config.settings import production
        importlib.reload(production)


def test_production_settings_rejects_wildcard_allowed_hosts(monkeypatch):
    """Verify production settings fails closed if ALLOWED_HOSTS is wildcard '*'."""
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.production")
    monkeypatch.setenv(
        "DJANGO_SECRET_KEY",
        "production-super-secret-key-of-at-least-fifty-characters-length-12345",
    )
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "*")

    with pytest.raises(ImproperlyConfigured):
        import importlib
        from config.settings import production
        importlib.reload(production)
