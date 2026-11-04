"""Recruitment CRM Object-Level and Role-Based Permission Classes."""
from rest_framework import permissions
from apps.accounts.models import RoleCatalog


class IsCrmStaffOrReadOnly(permissions.BasePermission):
    """Allows full CRUD to CRM Executives, Calling Executives, Placement Heads and Admins.

    Allows read-only access to Auditors. Denies all other roles.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        user_roles = request.user.get_roles()

        # Auditor is read-only
        if RoleCatalog.AUDITOR in user_roles and request.method in permissions.SAFE_METHODS:
            return True

        # Authorized CRM operating roles
        authorized_roles = [
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.CALLING_EXECUTIVE,
            RoleCatalog.CRM_EXECUTIVE,
        ]
        return any(role in user_roles for role in authorized_roles)


class CanManageCompany(permissions.BasePermission):
    """Object-level permission governing Company modification and reassignment.

    - Admins and Placement Heads can edit and reassign any company.
    - Calling Executives can edit their assigned company or unassigned leads.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Safe read methods are governed by IsCrmStaffOrReadOnly
        if request.method in permissions.SAFE_METHODS:
            return True

        user_roles = request.user.get_roles()

        if RoleCatalog.ADMIN in user_roles or RoleCatalog.PLACEMENT_HEAD in user_roles:
            return True

        if RoleCatalog.CALLING_EXECUTIVE in user_roles or RoleCatalog.CRM_EXECUTIVE in user_roles:
            # Can edit if assigned to them or if company is currently unassigned
            if obj.assigned_to is None or obj.assigned_to == request.user:
                return True

        return False


class CanManageFollowUp(permissions.BasePermission):
    """Governs completing, rescheduling, or cancelling follow-up tasks."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        user_roles = request.user.get_roles()
        if RoleCatalog.ADMIN in user_roles or RoleCatalog.PLACEMENT_HEAD in user_roles:
            return True

        # Assigned executive can update and complete their own tasks
        return obj.assigned_to == request.user

