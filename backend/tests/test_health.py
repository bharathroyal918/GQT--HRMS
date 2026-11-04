"""Health and Readiness Endpoint Tests."""
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_liveness_health_check():
    """Verify /api/v1/health/ returns 200 and expected status payload."""
    client = APIClient()
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert data["version"] == "1.0.0"


@pytest.mark.django_db
def test_readiness_probe_database_ok():
    """Verify /api/v1/ready/ verifies database connectivity."""
    client = APIClient()
    response = client.get("/api/v1/ready/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
