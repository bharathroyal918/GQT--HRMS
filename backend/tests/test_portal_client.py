"""Student Portal Client Gateway Tests."""
import pytest
from apps.portal.client import StudentPortalClient
from apps.portal.exceptions import PortalDisabledError


def test_portal_client_disabled_mode():
    """Verify portal client behaves safely when integration is disabled."""
    client = StudentPortalClient(enabled=False)
    assert not client.is_configured()

    ping_res = client.ping()
    assert ping_res["status"] == "mock"
    assert ping_res["enabled"] is False

    mock_student = client.fetch_student("1GQ21CS001")
    assert mock_student["usn"] == "1GQ21CS001"
    assert mock_student["mock"] is True


def test_portal_client_disabled_raises_on_direct_request():
    """Verify _execute_request raises PortalDisabledError when disabled."""
    client = StudentPortalClient(enabled=False)
    with pytest.raises(PortalDisabledError, match="disabled"):
        client._execute_request("GET", "health/")
