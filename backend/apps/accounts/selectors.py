"""Selectors (Read Operations) for Accounts & RBAC."""
from typing import Optional, List
from django.db.models import QuerySet
from apps.accounts.models import User, Role, UserRoleAssignment


def get_user_by_id(user_id: str) -> Optional[User]:
    """Retrieve user by UUID."""
    return User.objects.filter(id=user_id).first()


def get_user_by_email(email: str) -> Optional[User]:
    """Retrieve user by case-insensitive normalized email."""
    if not email:
        return None
    return User.objects.filter(email=email.strip().lower()).first()


def list_users(search: Optional[str] = None, role_code: Optional[str] = None, is_active: Optional[bool] = None) -> QuerySet[User]:
    """List users with optional search and role filtering."""
    qs = User.objects.all().prefetch_related("role_assignments__role").order_by("-created_at")

    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    if search:
        search = search.strip().lower()
        qs = qs.filter(email__icontains=search)

    if role_code:
        qs = qs.filter(role_assignments__role__code=role_code)

    return qs


def list_roles() -> QuerySet[Role]:
    """List all configured institutional roles."""
    return Role.objects.all().order_by("code")
