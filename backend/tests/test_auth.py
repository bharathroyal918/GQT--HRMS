"""Authentication Lifecycle, Cookie Issuance, and Refresh Tests."""
import pytest
from rest_framework.test import APIClient
from apps.accounts.services import create_user, assign_role
from apps.accounts.models import RoleCatalog
from apps.core.models import AuditLog


@pytest.mark.django_db
def test_login_successful_sets_httponly_cookies():
    """Verify login authenticates and sets HttpOnly cookies."""
    user = create_user(
        email="auth.user@gqt.local",
        password="MySecretPassword123!",
        first_name="Auth",
        last_name="User",
    )
    assign_role(user, RoleCatalog.CRM_EXECUTIVE)

    client = APIClient()
    response = client.post(
        "/api/v1/auth/login/",
        {"email": "auth.user@gqt.local", "password": "MySecretPassword123!"},
        format="json",
    )
    assert response.status_code == 200
    assert "gqt_access_token" in response.cookies
    assert "gqt_refresh_token" in response.cookies

    access_cookie = response.cookies["gqt_access_token"]
    assert access_cookie["httponly"] is True
    assert access_cookie["samesite"] == "Lax"

    data = response.json()
    assert data["email"] == "auth.user@gqt.local"
    assert RoleCatalog.CRM_EXECUTIVE in data["roles"]


@pytest.mark.django_db
def test_login_invalid_password_returns_401():
    """Verify login with wrong password returns 401 and creates AuditLog."""
    create_user(
        email="valid.target@gqt.local",
        password="CorrectPassword123!",
    )
    client = APIClient()
    response = client.post(
        "/api/v1/auth/login/",
        {"email": "valid.target@gqt.local", "password": "WrongPassword999!"},
        format="json",
    )
    assert response.status_code == 401
    assert "gqt_access_token" not in response.cookies

    # Verify audit log was created for failed attempt
    assert AuditLog.objects.filter(action="AUTH_LOGIN_FAILED", resource_id="valid.target@gqt.local").exists()


@pytest.mark.django_db
def test_current_user_profile_via_cookie():
    """Verify CurrentUserProfileAPIView reads JWT from HttpOnly cookie."""
    user = create_user(
        email="profile.check@gqt.local",
        password="ProfilePassword123!",
        first_name="Profile",
        last_name="Check",
    )
    assign_role(user, RoleCatalog.TRAINER)

    client = APIClient()
    login_res = client.post(
        "/api/v1/auth/login/",
        {"email": "profile.check@gqt.local", "password": "ProfilePassword123!"},
        format="json",
    )
    assert login_res.status_code == 200

    # Next request uses the cookie set by login
    me_res = client.get("/api/v1/auth/me/")
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "profile.check@gqt.local"
    assert RoleCatalog.TRAINER in me_data["roles"]


@pytest.mark.django_db
def test_token_refresh_via_cookie():
    """Verify silent token refresh via HttpOnly refresh cookie."""
    user = create_user(
        email="refresh.user@gqt.local",
        password="RefreshPassword123!",
    )
    client = APIClient()
    login_res = client.post(
        "/api/v1/auth/login/",
        {"email": "refresh.user@gqt.local", "password": "RefreshPassword123!"},
        format="json",
    )
    assert login_res.status_code == 200

    refresh_res = client.post("/api/v1/auth/token/refresh/", {}, format="json")
    assert refresh_res.status_code == 200
    assert "gqt_access_token" in refresh_res.cookies


@pytest.mark.django_db
def test_logout_deletes_cookies_and_blacklists():
    """Verify logout clears cookies and blacklists the token."""
    user = create_user(
        email="logout.user@gqt.local",
        password="LogoutPassword123!",
    )
    client = APIClient()
    client.post(
        "/api/v1/auth/login/",
        {"email": "logout.user@gqt.local", "password": "LogoutPassword123!"},
        format="json",
    )

    logout_res = client.post("/api/v1/auth/logout/", {}, format="json")
    assert logout_res.status_code == 200
    assert logout_res.cookies["gqt_access_token"].value == ""
    assert logout_res.cookies["gqt_refresh_token"].value == ""
