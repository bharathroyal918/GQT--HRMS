"""Integration tests for Audit Log & Compliance Oversight API endpoints."""
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import RoleCatalog
from apps.accounts.services import create_user, assign_role
from apps.core.models import AuditLog


@pytest.fixture
def admin_user(db):
    user = create_user(email="admin_audittest@gqt.local", password="Password@123", is_staff=True)
    assign_role(user, RoleCatalog.ADMIN)
    return user


@pytest.fixture
def auditor_user(db):
    user = create_user(email="auditor_audittest@gqt.local", password="Password@123")
    assign_role(user, RoleCatalog.AUDITOR)
    return user


@pytest.fixture
def caller_user(db):
    user = create_user(email="caller_audittest@gqt.local", password="Password@123")
    assign_role(user, RoleCatalog.CALLING_EXECUTIVE)
    return user


@pytest.fixture
def sample_audit_logs(db, admin_user):
    logs = [
        AuditLog.objects.create(
            user=admin_user,
            action="JOB_REQUIREMENT_APPROVED",
            resource_type="JobRequirement",
            resource_id="11111111-1111-1111-1111-111111111111",
            ip_address="127.0.0.1",
            changes={"status": ["PENDING_APPROVAL", "APPROVED"]},
            correlation_id="corr-test-1",
        ),
        AuditLog.objects.create(
            user=admin_user,
            action="CREATIVE_APPROVED",
            resource_type="CreativeRequest",
            resource_id="22222222-2222-2222-2222-222222222222",
            ip_address="127.0.0.1",
            changes={"status": ["UNDER_REVIEW", "APPROVED"]},
            correlation_id="corr-test-2",
        ),
        AuditLog.objects.create(
            user=None,
            action="SECURITY_ALERT",
            resource_type="System",
            resource_id="=cmd|' /C calc'!A0",
            ip_address="192.168.1.1",
            changes={},
            correlation_id="corr-test-3",
        ),
    ]
    return logs


@pytest.mark.django_db
def test_audit_log_list_unauthenticated_rejected():
    client = APIClient()
    response = client.get("/api/v1/audit-logs/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_audit_log_list_unauthorized_role_forbidden(caller_user):
    client = APIClient()
    client.force_authenticate(user=caller_user)
    response = client.get("/api/v1/audit-logs/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_audit_log_list_permitted_for_auditor(auditor_user, sample_audit_logs):
    client = APIClient()
    client.force_authenticate(user=auditor_user)
    response = client.get("/api/v1/audit-logs/")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert len(response.data["results"]) >= 3


@pytest.mark.django_db
def test_audit_log_filtering_by_action(auditor_user, sample_audit_logs):
    client = APIClient()
    client.force_authenticate(user=auditor_user)
    response = client.get("/api/v1/audit-logs/?action=JOB_REQUIREMENT_APPROVED")
    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    assert len(results) == 1
    assert results[0]["action"] == "JOB_REQUIREMENT_APPROVED"


@pytest.mark.django_db
def test_audit_summary_endpoint(auditor_user, sample_audit_logs):
    client = APIClient()
    client.force_authenticate(user=auditor_user)
    response = client.get("/api/v1/audit-logs/summary/")
    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert data["total_count"] >= 3
    assert "unique_actors" in data
    assert "top_actions" in data
    assert "recent_critical_actions" in data


@pytest.mark.django_db
def test_audit_log_csv_export_sanitizes_formula_injection(auditor_user, sample_audit_logs):
    client = APIClient()
    client.force_authenticate(user=auditor_user)
    response = client.get("/api/v1/audit-logs/export/")
    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"].startswith("text/csv")
    content = response.content.decode("utf-8")
    assert "'=cmd|" in content
