"""Services (Write Operations & Business Logic) for Accounts & RBAC."""
from typing import Optional, List, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import User, Role, UserRoleAssignment, RoleCatalog
from apps.core.models import AuditLog
from apps.core.middleware import get_current_correlation_id


@transaction.atomic
def create_user(
    email: str,
    password: Optional[str] = None,
    first_name: str = "",
    last_name: str = "",
    phone_number: str = "",
    role_codes: Optional[List[str]] = None,
    is_staff: bool = False,
    created_by: Optional[User] = None,
    ip_address: Optional[str] = None,
) -> User:
    """Create a new user, assign requested roles, and record an immutable audit log."""
    normalized_email = email.strip().lower()
    if User.objects.filter(email=normalized_email).exists():
        raise ValidationError(f"A user with email '{normalized_email}' already exists.")

    user = User.objects.create_user(
        email=normalized_email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        is_staff=is_staff,
    )

    assigned_roles = []
    if role_codes:
        for code in role_codes:
            role, _ = Role.objects.get_or_create(code=code, defaults={"name": code.replace("_", " ").title()})
            UserRoleAssignment.objects.create(
                user=user,
                role=role,
                assigned_by=created_by,
            )
            assigned_roles.append(code)

    AuditLog.objects.create(
        user=created_by,
        action="USER_CREATED",
        resource_type="accounts.User",
        resource_id=str(user.id),
        ip_address=ip_address,
        correlation_id=get_current_correlation_id(),
        changes={
            "email": user.email,
            "roles": assigned_roles,
            "is_staff": user.is_staff,
        },
    )

    return user


@transaction.atomic
def assign_role(
    user: User,
    role_code: str,
    assigned_by: Optional[User] = None,
    ip_address: Optional[str] = None,
) -> UserRoleAssignment:
    """Assign an operational role to a user."""
    role, _ = Role.objects.get_or_create(code=role_code, defaults={"name": role_code.replace("_", " ").title()})
    assignment, created = UserRoleAssignment.objects.get_or_create(
        user=user,
        role=role,
        defaults={"assigned_by": assigned_by},
    )

    if created:
        AuditLog.objects.create(
            user=assigned_by,
            action="ROLE_ASSIGNED",
            resource_type="accounts.UserRoleAssignment",
            resource_id=str(assignment.id),
            ip_address=ip_address,
            correlation_id=get_current_correlation_id(),
            changes={"user_email": user.email, "role_code": role_code},
        )

    return assignment


@transaction.atomic
def revoke_role(
    user: User,
    role_code: str,
    revoked_by: Optional[User] = None,
    ip_address: Optional[str] = None,
) -> bool:
    """Revoke an operational role from a user."""
    assignment = UserRoleAssignment.objects.filter(user=user, role__code=role_code).first()
    if assignment:
        assignment_id = str(assignment.id)
        assignment.delete()
        AuditLog.objects.create(
            user=revoked_by,
            action="ROLE_REVOKED",
            resource_type="accounts.UserRoleAssignment",
            resource_id=assignment_id,
            ip_address=ip_address,
            correlation_id=get_current_correlation_id(),
            changes={"user_email": user.email, "role_code": role_code},
        )
        return True
    return False


@transaction.atomic
def set_user_active_status(
    user: User,
    is_active: bool,
    updated_by: Optional[User] = None,
    ip_address: Optional[str] = None,
) -> User:
    """Activate or deactivate a user account."""
    user.is_active = is_active
    user.save(update_fields=["is_active", "updated_at"])

    AuditLog.objects.create(
        user=updated_by,
        action="USER_STATUS_UPDATED",
        resource_type="accounts.User",
        resource_id=str(user.id),
        ip_address=ip_address,
        correlation_id=get_current_correlation_id(),
        changes={"is_active": is_active},
    )
    return user


def generate_jwt_tokens_for_user(user: User) -> Tuple[str, str]:
    """Generate SimpleJWT access and refresh tokens for an authenticated user."""
    refresh = RefreshToken.for_user(user)
    # Include roles in access token claims for downstream inspectability
    refresh["roles"] = user.get_roles()
    refresh["email"] = user.email
    return str(refresh.access_token), str(refresh)
