"""Accounts, Identity, and Role-Based Access Control (RBAC) Models."""
import uuid
from typing import List
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.conf import settings


class RoleCatalog:
    """Standardized operational role codes derived from approved GQT recruitment requirements."""

    ADMIN = "ADMIN"
    PLACEMENT_HEAD = "PLACEMENT_HEAD"
    PLACEMENT_OFFICER = "PLACEMENT_OFFICER"
    CALLING_EXECUTIVE = "CALLING_EXECUTIVE"
    CRM_EXECUTIVE = "CRM_EXECUTIVE"
    CREATIVE_DESIGNER = "CREATIVE_DESIGNER"
    CREATIVE_REVIEWER = "CREATIVE_REVIEWER"
    TRAINER = "TRAINER"
    INTERVIEW_COORDINATOR = "INTERVIEW_COORDINATOR"
    AUDITOR = "AUDITOR"

    CHOICES = (
        (ADMIN, "System Administrator"),
        (PLACEMENT_HEAD, "Placement Head / Approver"),
        (PLACEMENT_OFFICER, "Placement Officer"),
        (CALLING_EXECUTIVE, "Company Acquisition / Calling Executive"),
        (CRM_EXECUTIVE, "Recruitment CRM Executive"),
        (CREATIVE_DESIGNER, "Design Team / Creative Designer"),
        (CREATIVE_REVIEWER, "Creative Reviewer / Approver"),
        (TRAINER, "Student Preparation / Trainer"),
        (INTERVIEW_COORDINATOR, "Interview Coordinator"),
        (AUDITOR, "Reporting / Compliance Auditor"),
    )

    @classmethod
    def all_roles(cls) -> list[str]:
        return [choice[0] for choice in cls.CHOICES]


class UserManager(BaseUserManager):
    """Custom manager for email-based authentication and user lifecycle."""

    def normalize_email(self, email: str | None) -> str:
        """Case-insensitively normalize and lowercase the email address."""
        email = super().normalize_email(email or "")
        return email.lower().strip()

    def create_user(self, email: str, password: str | None = None, **extra_fields) -> "User":
        """Create and persist a regular user with a normalized email and hashed password."""
        if not email:
            raise ValueError("An email address is required to register an account.")

        normalized_email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=normalized_email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> "User":
        """Create and persist an administrator with superuser and staff flags."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser accounts must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser accounts must have is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with UUID primary key and normalized email as the authentication identity."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Cryptographically random UUIDv4 primary key.",
    )
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Normalized email address used as the primary login identifier.",
    )
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    phone_number = models.CharField(max_length=20, blank=True, default="")

    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this user account is active and permitted to login.",
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into the Django admin site.",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "accounts_user"
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email

    def get_roles(self) -> List[str]:
        """Return list of active role codes assigned to this user."""
        return list(
            self.role_assignments.select_related("role").values_list("role__code", flat=True)
        )

    @property
    def role_codes(self) -> List[str]:
        """Convenience property for list of assigned role codes."""
        return self.get_roles()

    def has_role(self, role_code: str) -> bool:
        """Check if user holds an active role assignment."""
        if self.is_superuser:
            return True
        return self.role_assignments.filter(role__code=role_code).exists()

    def has_any_role(self, *role_codes: str) -> bool:
        """Check if user holds any of the specified roles."""
        if self.is_superuser:
            return True
        return self.role_assignments.filter(role__code__in=role_codes).exists()


class Role(models.Model):
    """Institutional role entity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True, choices=RoleCatalog.CHOICES, db_index=True)
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_role"
        ordering = ["code"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class UserRoleAssignment(models.Model):
    """Mapping between a user and an operational role."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="role_assignments",
        db_index=True,
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_assignments",
        db_index=True,
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="roles_assigned_by_me",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_user_role"
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="unique_user_role_assignment")
        ]
        verbose_name = "User Role Assignment"
        verbose_name_plural = "User Role Assignments"

    def __str__(self) -> str:
        return f"{self.user.email} -> {self.role.code}"
