"""Job Requirements Object-Level and Role-Based Permission Classes.

Strictly enforces Segregation of Duties (SoD), Auditor read-only restrictions,
and deny-by-default access policies.
"""
from rest_framework import permissions
from apps.accounts.models import RoleCatalog


class IsJobStaffOrReadOnly(permissions.BasePermission):
    """Allows staff roles to access job requirements.

    - ADMIN and PLACEMENT_HEAD have full operational privileges.
    - PLACEMENT_OFFICER has creation, submission, and verification privileges.
    - AUDITOR has strictly read-only access (SAFE_METHODS).
    - Other staff (CALLING_EXECUTIVE, CRM_EXECUTIVE) have read-only access for coordination.
    - Unauthenticated users and students are denied.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        user_roles = request.user.get_roles()

        # Auditor is strictly read-only
        if RoleCatalog.AUDITOR in user_roles:
            return request.method in permissions.SAFE_METHODS

        # Coordination roles are read-only
        if any(r in user_roles for r in [RoleCatalog.CALLING_EXECUTIVE, RoleCatalog.CRM_EXECUTIVE]):
            return request.method in permissions.SAFE_METHODS

        # Operational job roles
        authorized_roles = [
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
        ]
        return any(role in user_roles for role in authorized_roles)


class CanVerifyJob(permissions.BasePermission):
    """Governs updating 5-point verification checks.

    Allowed for PLACEMENT_OFFICER, PLACEMENT_HEAD, and ADMIN.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        user_roles = request.user.get_roles()
        if RoleCatalog.AUDITOR in user_roles:
            return False

        return any(
            role in user_roles
            for role in [RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD, RoleCatalog.PLACEMENT_OFFICER]
        )


class CanApproveOrRejectJob(permissions.BasePermission):
    """Governs final approval, rejection, and authorized amendment.

    Restricted strictly to PLACEMENT_HEAD and ADMIN roles.
    Placement Officers and Auditors are strictly forbidden.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        user_roles = request.user.get_roles()
        return any(role in user_roles for role in [RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD])

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Segregation of Duties: Submitter cannot approve their own job
        if obj.submitted_by_id == request.user.id and view.action == "approve":
            return False

        return self.has_permission(request, view)

