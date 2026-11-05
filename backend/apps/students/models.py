"""Student Management, Resume Vault, and Eligibility Models (MOD-005)."""
import uuid
import hashlib
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class PlacementStatusChoices(models.TextChoices):
    SEEKING = "SEEKING", "Seeking Placement"
    PLACED = "PLACED", "Placed / Offer Accepted"
    OPTED_OUT = "OPTED_OUT", "Opted Out of Placement"
    INELIGIBLE = "INELIGIBLE", "Ineligible / Suspended"


class RegistrationStatusChoices(models.TextChoices):
    REGISTERED = "REGISTERED", "Registered for Drive"
    SHORTLISTED = "SHORTLISTED", "Shortlisted by Recruiter"
    REJECTED = "REJECTED", "Not Shortlisted"
    WITHDRAWN = "WITHDRAWN", "Withdrawn by Candidate"


class CohortStatusChoices(models.TextChoices):
    DRAFT = "DRAFT", "Draft Assembly"
    FINALIZED = "FINALIZED", "Finalized for Training & Review"
    LOCKED = "LOCKED", "Locked for Recruiter Dispatch"


class StudentProfile(TimeStampedModel):
    """Master candidate entity representing an enrolled student eligible for placement services."""

    roll_number = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Institutional registration or roll number.",
    )
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=32)
    degree = models.CharField(max_length=64, default="B.Tech")
    branch = models.CharField(max_length=64, db_index=True, help_text="Academic discipline (e.g. CSE, ECE, MCA)")
    graduation_year = models.IntegerField(db_index=True, help_text="Graduation batch year (e.g. 2025)")
    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Cumulative Grade Point Average (0.00 - 10.00).",
    )
    backlogs_count = models.PositiveSmallIntegerField(
        default=0,
        help_text="Count of current active academic backlogs.",
    )
    tenth_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Class 10 aggregate percentage.",
    )
    twelfth_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Class 12 / Diploma aggregate percentage.",
    )
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text="Verified student technical skill tags.",
    )
    placement_status = models.CharField(
        max_length=32,
        choices=PlacementStatusChoices.choices,
        default=PlacementStatusChoices.SEEKING,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True, help_text="Internal coordinator or trainer notes.")

    class Meta:
        db_table = "students_profile"
        ordering = ["roll_number"]

    def __str__(self) -> str:
        return f"{self.roll_number} - {self.full_name} ({self.branch} {self.graduation_year})"


class StudentResume(TimeStampedModel):
    """Versioned PDF resume vault with cryptographic integrity digest."""

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="resumes",
    )
    version = models.PositiveSmallIntegerField(default=1)
    file_name = models.CharField(max_length=255)
    file_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 integrity hash of the uploaded resume.",
    )
    file_size_bytes = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(
        default=False,
        help_text="Flag indicating ATS/placement quality sign-off by trainer.",
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_resumes",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "students_resume"
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "version"],
                name="unique_resume_version_per_student",
            )
        ]

    def __str__(self) -> str:
        return f"{self.student.roll_number} Resume v{self.version} ({'Verified' if self.is_verified else 'Unverified'})"


class DriveRegistration(TimeStampedModel):
    """Registration record of a candidate registering for a published job requirement."""

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="drive_registrations",
    )
    job = models.ForeignKey(
        "jobs.JobRequirement",
        on_delete=models.CASCADE,
        related_name="candidate_registrations",
    )
    status = models.CharField(
        max_length=32,
        choices=RegistrationStatusChoices.choices,
        default=RegistrationStatusChoices.REGISTERED,
        db_index=True,
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "students_drive_registration"
        ordering = ["-registered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "job"],
                name="unique_candidate_registration_per_job",
            )
        ]

    def __str__(self) -> str:
        return f"{self.student.roll_number} registered for {self.job.title} ({self.status})"


class EligibilityEvaluation(TimeStampedModel):
    """Deterministic snapshot record evaluating student eligibility against a JobRequirement."""

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="eligibility_evaluations",
    )
    job = models.ForeignKey(
        "jobs.JobRequirement",
        on_delete=models.CASCADE,
        related_name="candidate_evaluations",
    )
    is_eligible = models.BooleanField(default=False, db_index=True)
    failed_criteria = models.JSONField(
        default=list,
        blank=True,
        help_text="List of failure reason strings (e.g. ['CGPA 6.2 < 7.0', 'Branch ME not in [CSE, IT]'])",
    )
    evaluated_at = models.DateTimeField(auto_now_add=True)
    manually_overridden = models.BooleanField(default=False)
    overridden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authorized_eligibility_overrides",
    )
    override_reason = models.TextField(blank=True)

    class Meta:
        db_table = "students_eligibility_evaluation"
        ordering = ["-evaluated_at"]

    def __str__(self) -> str:
        res = "ELIGIBLE" if self.is_eligible or self.manually_overridden else "INELIGIBLE"
        return f"{self.student.roll_number} -> {self.job.title}: {res}"


class CandidateCohort(TimeStampedModel):
    """Finalized and locked cohort roster for a specific placement drive."""

    job = models.OneToOneField(
        "jobs.JobRequirement",
        on_delete=models.CASCADE,
        related_name="candidate_cohort",
    )
    students = models.ManyToManyField(
        StudentProfile,
        related_name="participating_cohorts",
        blank=True,
    )
    status = models.CharField(
        max_length=32,
        choices=CohortStatusChoices.choices,
        default=CohortStatusChoices.DRAFT,
        db_index=True,
    )
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="finalized_cohorts",
    )
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "students_candidate_cohort"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Cohort for {self.job.title} ({self.status}, {self.students.count()} students)"
