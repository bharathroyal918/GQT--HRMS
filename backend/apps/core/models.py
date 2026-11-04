"""Core architectural models: TimeStampedModel and immutable AuditLog."""
import uuid
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model supplying UUID primary key, timestamps, and soft deletion."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Cryptographically secure, non-enumerable primary key.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="UTC timestamp when the record was initially created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="UTC timestamp when the record was last modified.",
    )
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Soft deletion flag to maintain historical referential integrity.",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class AuditLogQuerySet(models.QuerySet):
    """Custom QuerySet preventing bulk deletion and modification of audit records."""

    def delete(self):
        raise PermissionError("Audit logs are strictly immutable and cannot be deleted via bulk operations.")

    def update(self, **kwargs):
        raise PermissionError("Audit logs are strictly immutable and cannot be modified via bulk operations.")


class AuditLogManager(models.Manager.from_queryset(AuditLogQuerySet)):
    """Manager enforcing append-only immutability across querysets."""
    pass


class AuditLog(models.Model):
    """Immutable audit trail recording administrative and domain actions across the platform."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=128, db_index=True)
    resource_type = models.CharField(max_length=128, db_index=True)
    resource_id = models.CharField(max_length=128, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    changes = models.JSONField(default=dict, blank=True)
    correlation_id = models.CharField(max_length=64, db_index=True, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = AuditLogManager()

    class Meta:
        db_table = "core_audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit logs are strictly immutable and cannot be deleted.")

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise PermissionError("Audit logs are strictly immutable and cannot be modified after creation.")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.created_at.isoformat()} | {self.action} on {self.resource_type}:{self.resource_id}"
