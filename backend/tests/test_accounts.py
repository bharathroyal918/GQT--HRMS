"""User and Role Model & Service Tests."""
import uuid
import pytest
from apps.accounts.models import User, RoleCatalog
from apps.accounts.services import create_user, assign_role, revoke_role


@pytest.mark.django_db
def test_create_user_uuid_and_normalization():
    """Verify user primary key is UUID and email is lowercased and trimmed."""
    user = create_user(
        email="  Test.Officer@GQT.Local  ",
        password="SecurePassword123!",
        first_name="Jane",
        last_name="Doe",
    )
    assert isinstance(user.id, uuid.UUID)
    assert user.email == "test.officer@gqt.local"
    assert user.check_password("SecurePassword123!")
    assert not user.check_password("WrongPassword")
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_role_catalog_contains_ten_roles():
    """Verify that all 10 canonical roles are recognized."""
    roles = RoleCatalog.all_roles()
    assert len(roles) == 10
    expected_roles = [
        "ADMIN",
        "PLACEMENT_HEAD",
        "PLACEMENT_OFFICER",
        "CALLING_EXECUTIVE",
        "CRM_EXECUTIVE",
        "CREATIVE_DESIGNER",
        "CREATIVE_REVIEWER",
        "TRAINER",
        "INTERVIEW_COORDINATOR",
        "AUDITOR",
    ]
    for r in expected_roles:
        assert r in roles


@pytest.mark.django_db
def test_assign_and_revoke_role():
    """Verify role assignment and revocation services."""
    user = create_user(
        email="role.test@gqt.local",
        password="ValidPassword123!",
        first_name="Role",
        last_name="Tester",
    )
    assert not user.has_role(RoleCatalog.PLACEMENT_OFFICER)

    # Assign role
    assignment = assign_role(user=user, role_code=RoleCatalog.PLACEMENT_OFFICER)
    assert assignment.role.code == RoleCatalog.PLACEMENT_OFFICER
    assert user.has_role(RoleCatalog.PLACEMENT_OFFICER)
    assert RoleCatalog.PLACEMENT_OFFICER in user.role_codes

    # Revoke role
    revoked = revoke_role(user=user, role_code=RoleCatalog.PLACEMENT_OFFICER)
    assert revoked is True
    assert not user.has_role(RoleCatalog.PLACEMENT_OFFICER)


@pytest.mark.django_db
def test_create_superuser():
    """Verify superuser creation via manager."""
    admin_user = User.objects.create_superuser(
        email="admin.root@gqt.local",
        password="SuperAdminPassword123!",
    )
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
    assert admin_user.has_role(RoleCatalog.ADMIN)
