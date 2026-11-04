"""Audit Logging, Correlation ID Middleware, and Sensitive Data Filter Tests."""
import logging
import pytest
from rest_framework.test import APIClient
from apps.core.models import AuditLog
from apps.core.logging import SensitiveDataFilter


@pytest.mark.django_db
def test_audit_log_immutability():
    """Verify AuditLog records cannot be deleted via ORM delete()."""
    log_entry = AuditLog.objects.create(
        action="TEST_ACTION",
        resource_type="TestEntity",
        resource_id="123",
        changes={"field": "value"},
    )
    assert log_entry.id is not None

    with pytest.raises(PermissionError, match="Audit logs are strictly immutable"):
        log_entry.delete()

    # Verify log still exists in DB
    assert AuditLog.objects.filter(id=log_entry.id).exists()


@pytest.mark.django_db
def test_audit_log_bulk_operations_and_update_immutability():
    """Verify bulk delete(), bulk update(), and instance save() modifications are blocked."""
    log_entry = AuditLog.objects.create(
        action="CREATIVE_VERSION_APPROVED",
        resource_type="creatives.CreativeAssetVersion",
        resource_id="v-12345",
        changes={"status": "APPROVED"},
    )

    # 1. Bulk delete is blocked
    with pytest.raises(PermissionError, match="cannot be deleted via bulk operations"):
        AuditLog.objects.filter(id=log_entry.id).delete()

    # 2. Bulk update is blocked
    with pytest.raises(PermissionError, match="cannot be modified via bulk operations"):
        AuditLog.objects.filter(id=log_entry.id).update(action="TAMPERED_ACTION")

    # 3. Instance update via save() is blocked
    log_entry.action = "TAMPERED_ACTION"
    with pytest.raises(PermissionError, match="cannot be modified after creation"):
        log_entry.save()

    # Verify log entry in DB remains unchanged
    refreshed = AuditLog.objects.get(id=log_entry.id)
    assert refreshed.action == "CREATIVE_VERSION_APPROVED"


@pytest.mark.django_db
def test_correlation_id_middleware_and_header():
    """Verify responses include X-Correlation-ID header."""
    client = APIClient()
    response = client.get("/api/v1/health/")
    assert "X-Correlation-ID" in response.headers
    corr_id = response.headers["X-Correlation-ID"]
    assert len(corr_id) == 36  # UUID format


def test_sensitive_data_filter_masks_secrets():
    """Verify SensitiveDataFilter redacts passwords and tokens in log records."""
    log_filter = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="User login attempt with password=MySecret123 and token: bearer eyJhbGciOiJIUzI1NiJ9",
        args=(),
        exc_info=None,
    )
    passed = log_filter.filter(record)
    assert passed is True
    assert "MySecret123" not in record.msg
    assert "bearer eyJ" not in record.msg
    assert "[REDACTED]" in record.msg
