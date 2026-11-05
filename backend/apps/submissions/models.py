"""Candidate Submissions & Profile Dispatch Models (MOD-007)."""
import uuid
import hashlib
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class SubmissionStatusChoices(models.TextChoices):
    DRAFT = "DRAFT", "Draft Assembly"
    READY_FOR_REVIEW = "READY_FOR_REVIEW", "Ready for Placement Head Sign-Off"
    APPROVED = "APPROVED", "Approved for Recruiter Dispatch"
    DISPATCHED = "DISPATCHED", "Dispatched to Recruiter"
    ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged by Corporate Recruiter"


class SubmissionPackage(TimeStampedModel):
    """Container grouping certified candidates submitted to a corporate partner."""

    job = models.ForeignKey(
        "jobs.JobRequirement",
        on_delete=models.CASCADE,
        related_name="submission_packages",
    )
    package_code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Standardized submission package identifier (e.g. SUB-2026-001).",
    )
    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=SubmissionStatusChoices.choices,
        default=SubmissionStatusChoices.DRAFT,
        db_index=True,
    )
    roster_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 cryptographic digest of the candidate roster.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_submission_packages",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_submission_packages",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "submissions_package"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.package_code}: {self.title} ({self.status})"


class SubmissionItem(TimeStampedModel):
    """Individual candidate record included in a SubmissionPackage."""

    package = models.ForeignKey(
        SubmissionPackage,
        on_delete=models.CASCADE,
        related_name="items",
    )
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="submission_records",
    )
    resume_version = models.PositiveSmallIntegerField(default=1)
    is_shortlisted = models.BooleanField(
        default=False,
        help_text="Flag indicating whether corporate recruiter shortlisted this candidate.",
    )

    class Meta:
        db_table = "submissions_item"
        ordering = ["student__roll_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["package", "student"],
                name="unique_candidate_per_submission_package",
            )
        ]

    def __str__(self) -> str:
        return f"{self.package.package_code} -> {self.student.roll_number}"


class DispatchLog(TimeStampedModel):
    """Audit log tracking transmission of profile packages to corporate recruiters."""

    package = models.ForeignKey(
        SubmissionPackage,
        on_delete=models.CASCADE,
        related_name="dispatch_logs",
    )
    channel = models.CharField(max_length=32, default="EMAIL")
    recipient_email = models.EmailField()
    recipient_name = models.CharField(max_length=255, blank=True)
    dispatched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logged_dispatches",
    )
    dispatched_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "submissions_dispatch_log"
        ordering = ["-dispatched_at"]

    def __str__(self) -> str:
        return f"Dispatch {self.package.package_code} to {self.recipient_email} at {self.dispatched_at}"

