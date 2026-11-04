"""RBAC and Permission Enforcement Tests."""
import pytest
from rest_framework.test import APIClient
from apps.accounts.services import create_user, assign_role
from apps.accounts.models import RoleCatalog


@pytest.mark.django_db
def test_deny_by_default_unauthenticated():
    """Verify protected user management endpoints reject unauthenticated requests."""
    client = APIClient()
    response = client.get("/api/v1/auth/users/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_user_management_forbidden_for_non_admin():
    """Verify staff member without Admin role cannot list or create users."""
    staff = create_user(
        email="caller.staff@gqt.local",
        password="CallerPassword123!",
    )
    assign_role(staff, RoleCatalog.CALLING_EXECUTIVE)

    client = APIClient()
    client.force_authenticate(user=staff)

    response = client.get("/api/v1/auth/users/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_user_management_permitted_for_admin():
    """Verify administrator can list and provision users."""
    admin_user = create_user(
        email="admin.manager@gqt.local",
        password="AdminPassword123!",
        is_staff=True,
    )
    assign_role(admin_user, RoleCatalog.ADMIN)

    client = APIClient()
    client.force_authenticate(user=admin_user)

    response = client.get("/api/v1/auth/users/")
    assert response.status_code == 200

    create_res = client.post(
        "/api/v1/auth/users/",
        {
            "email": "new.recruit@gqt.local",
            "password": "NewRecruitPassword123!",
            "first_name": "New",
            "last_name": "Recruit",
            "roles": [RoleCatalog.CREATIVE_DESIGNER],
        },
        format="json",
    )
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["email"] == "new.recruit@gqt.local"
    assert RoleCatalog.CREATIVE_DESIGNER in created_data["roles"]
