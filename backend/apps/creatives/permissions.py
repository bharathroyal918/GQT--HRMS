"""RBAC and Segregation of Duties (SoD) Permission Classes for Creative Studio."""
from rest_framework import permissions
from apps.accounts.models import RoleCatalog


class IsCreativeStaffOrReadOnly(permissions.BasePermission):
    """Denies unauthenticated users and students. Grants read-only to AUDITOR."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Explicitly forbid students
        user_roles = set(user.get_roles())
        if "STUDENT" in user_roles and not (user.is_staff or user.is_superuser):
            return False

        # Auditor is strictly read-only
        if RoleCatalog.AUDITOR in user_roles:
            return request.method in permissions.SAFE_METHODS

        # Read-only methods allowed for authenticated staff/auditors
        if request.method in permissions.SAFE_METHODS:
            return True

        # Modification requires active operational creative/placement role
        operational_roles = {
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.CREATIVE_REVIEWER,
            RoleCatalog.CREATIVE_DESIGNER,
        }
        return bool(user_roles & operational_roles or user.is_superuser)


class CanCreateCreativeRequest(permissions.BasePermission):
    """Placement Officers, Placement Heads, Reviewers, and Admins can create requisitions."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        allowed_roles = {
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.CREATIVE_REVIEWER,
        }
        user_roles = set(user.get_roles())
        return bool(user_roles & allowed_roles)


class CanTriageOrAssignCreative(permissions.BasePermission):
    """Placement Heads, Creative Reviewers, and Admins can assign requisitions."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        allowed_roles = {
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.CREATIVE_REVIEWER,
        }
        user_roles = set(user.get_roles())
        return bool(user_roles & allowed_roles)


class CanReviewOrApproveCreative(permissions.BasePermission):
    """Placement Heads, Creative Reviewers, and Admins can perform review actions.
    Note: Segregation of Duties (SoD) against self-approval is strictly verified
    in the service layer against the version uploader.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        allowed_roles = {
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.CREATIVE_REVIEWER,
        }
        user_roles = set(user.get_roles())
        return bool(user_roles & allowed_roles)
