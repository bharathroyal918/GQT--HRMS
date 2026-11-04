"""Job Requirements, Verification, and Approval Domain Models.

Enforces five-point mandatory verification checklist, segregation of duties,
historical record preservation, and comprehensive audit history.
"""
import uuid
from decimal import Decimal
from typing import List, Dict, Any
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from apps.core.models import TimeStampedModel


class RoleCategoryChoices(models.TextChoices):
    SOFTWARE_ENGINEERING = "SOFTWARE_ENGINEERING", "Software Engineering / Developer"
    DATA_ANALYTICS = "DATA_ANALYTICS", "Data Analytics / Data Science"
    CLOUD_DEVOPS = "CLOUD_DEVOPS", "Cloud Computing & DevOps"
    QA_TESTING = "QA_TESTING", "Quality Assurance & Testing"
    PRODUCT_SUPPORT = "PRODUCT_SUPPORT", "Technical Support / IT Operations"
    CYBERSECURITY = "CYBERSECURITY", "Information Security & Cybersecurity"
    BUSINESS_ANALYST = "BUSINESS_ANALYST", "Business Analysis & Product Consulting"
    OTHER = "OTHER", "Other Domain / Multidisciplinary"


class WorkArrangementChoices(models.TextChoices):
    ONSITE = "ONSITE", "On-site / In-Office"
    HYBRID = "HYBRID", "Hybrid Model"
    REMOTE = "REMOTE", "Full Remote / Work from Home"


class JobStatusChoices(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PENDING_VERIFICATION = "PENDING_VERIFICATION", "Pending Verification"
    UNDER_VERIFICATION = "UNDER_VERIFICATION", "Under Verification Review"
    CHANGES_REQUESTED = "CHANGES_REQUESTED", "Changes Requested"
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Placement Head Approval"
    APPROVED = "APPROVED", "Approved & Verified"
    REJECTED = "REJECTED", "Rejected"


class VerificationCheckTypeChoices(models.TextChoices):
    ELIGIBILITY = "ELIGIBILITY", "Check 1: Eligibility Compliance"
    SALARY_AUTHENTICITY = "SALARY_AUTHENTICITY", "Check 2: Salary Authenticity & CTC"
    COMPANY_AUTHENTICITY = "COMPANY_AUTHENTICITY", "Check 3: Company & Contact Legitimacy"
    INTERVIEW_PROCESS = "INTERVIEW_PROCESS", "Check 4: Interview Process & Stages"
    REGISTRATION_DEADLINE = "REGISTRATION_DEADLINE", "Check 5: Registration Deadline Validity"


class CheckStatusChoices(models.TextChoices):
    PENDING = "PENDING", "Pending Review"
    VERIFIED = "VERIFIED", "Verified & Passed"
    FLAGGED = "FLAGGED", "Flagged for Attention"
    REJECTED = "REJECTED", "Rejected / Non-Compliant"


class JobRequirement(TimeStampedModel):
    """Structured job requirement specification requiring 5-point verification and independent approval."""

    company = models.ForeignKey(
        "crm.Company",
        on_delete=models.PROTECT,
        related_name="jobs",
        help_text="Corporate entity offering the position. Preserved via PROTECT deletion policy.",
        db_index=True,
    )
    title = models.CharField(max_length=255, db_index=True, help_text="Job role / designation")
    description = models.TextField(help_text="Detailed job description and responsibilities")
    role_category = models.CharField(
        max_length=64,
        choices=RoleCategoryChoices.choices,
        default=RoleCategoryChoices.SOFTWARE_ENGINEERING,
        db_index=True,
    )
    required_skills = models.JSONField(
        default=list,
        blank=True,
        help_text="List of mandatory technical and domain competencies",
    )

    # Academic & Eligibility Criteria
    min_cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum CGPA required (0.00 to 10.00)",
    )
    min_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum aggregate percentage required (0.00 to 100.00%)",
    )
    eligible_batches = models.JSONField(
        default=list,
        blank=True,
        help_text="Eligible passing out years (e.g., ['2024', '2025'])",
    )
    eligible_branches = models.JSONField(
        default=list,
        blank=True,
        help_text="Eligible academic disciplines (e.g., ['CSE', 'ECE', 'ISE', 'MCA'])",
    )
    max_backlogs_allowed = models.PositiveSmallIntegerField(
        default=0,
        help_text="Maximum permissible active backlogs",
    )

    # Compensation Structure
    min_ctc_lpa = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Minimum annual CTC in Lakhs Per Annum (LPA)",
    )
    max_ctc_lpa = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Maximum annual CTC in Lakhs Per Annum (LPA)",
    )
    stipend_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monthly stipend in INR if internship component exists",
    )
    salary_details = models.TextField(
        blank=True,
        default="",
        help_text="Breakdown of fixed, variable, perks, and probation compensation",
    )

    # Location & Work Arrangement
    job_location = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Primary job location or cities",
    )
    work_arrangement = models.CharField(
        max_length=32,
        choices=WorkArrangementChoices.choices,
        default=WorkArrangementChoices.ONSITE,
    )

    # Service Agreement / Bond
    has_bond = models.BooleanField(
        default=False,
        help_text="Whether candidates must sign an employment service agreement",
    )
    bond_duration_months = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Duration of service bond in months",
    )
    bond_details = models.TextField(
        blank=True,
        default="",
        help_text="Terms, penalty clauses, or conditions of service bond",
    )

    # Hiring Process & Deadlines
    interview_rounds = models.JSONField(
        default=list,
        blank=True,
        help_text="Ordered list of interview stages: [{'round_number': 1, 'round_type': 'APTITUDE', ...}]",
    )
    interview_process_notes = models.TextField(
        blank=True,
        default="",
        help_text="Evaluation criteria, mode (online/offline), and round sequence",
    )
    interview_date = models.DateField(
        null=True,
        blank=True,
        help_text="Scheduled date for primary campus drive or initial round",
    )
    registration_deadline = models.DateTimeField(
        help_text="Strict cutoff timestamp for student applications",
        db_index=True,
    )
    vacancies_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Estimated open positions",
    )

    # Ownership, Workflow, and Approval Metadata
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_jobs",
        help_text="Placement Officer who created and submitted this requirement",
    )
    assigned_verifier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_job_verifications",
        help_text="Staff member assigned to execute the 5-point verification checklist",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_jobs",
        help_text="Placement Head / Admin who authorized and approved this job",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_jobs",
        help_text="Placement Head / Admin who rejected this job",
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Documented justification for rejecting the requirement",
    )
    changes_requested_reason = models.TextField(
        blank=True,
        default="",
        help_text="Specific corrections requested by reviewer or approver",
    )

    status = models.CharField(
        max_length=32,
        choices=JobStatusChoices.choices,
        default=JobStatusChoices.DRAFT,
        db_index=True,
    )
    revision_number = models.PositiveIntegerField(
        default=1,
        help_text="Monotonically increasing version counter incremented on authorized amendments",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_jobs",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_jobs",
    )

    class Meta:
        db_table = "jobs_requirement"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["company", "status"]),
            models.Index(fields=["registration_deadline"]),
        ]
        verbose_name = "Job Requirement"
        verbose_name_plural = "Job Requirements"

    def __str__(self) -> str:
        return f"{self.title} at {self.company.name} ({self.status})"

    def clean(self):
        super().clean()
        errors = {}

        if self.min_ctc_lpa is not None and self.max_ctc_lpa is not None:
            if self.min_ctc_lpa < Decimal("0.00"):
                errors["min_ctc_lpa"] = "Minimum CTC cannot be negative."
            if self.max_ctc_lpa < Decimal("0.00"):
                errors["max_ctc_lpa"] = "Maximum CTC cannot be negative."
            if self.min_ctc_lpa > self.max_ctc_lpa:
                errors["max_ctc_lpa"] = "Maximum CTC must be greater than or equal to minimum CTC."

        if self.min_cgpa is not None:
            if self.min_cgpa < Decimal("0.00") or self.min_cgpa > Decimal("10.00"):
                errors["min_cgpa"] = "Minimum CGPA must be between 0.00 and 10.00."

        if self.min_percentage is not None:
            if self.min_percentage < Decimal("0.00") or self.min_percentage > Decimal("100.00"):
                errors["min_percentage"] = "Minimum percentage must be between 0.00 and 100.00."

        if self.has_bond:
            if not self.bond_duration_months or self.bond_duration_months <= 0:
                errors["bond_duration_months"] = "Bond duration in months is required when a service bond applies."

        if self.interview_date and self.registration_deadline:
            if self.interview_date < self.registration_deadline.date():
                errors["interview_date"] = "Interview date cannot precede the registration deadline."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_all_checks_verified(self) -> bool:
        """Returns True if and only if all five mandatory verification checks are VERIFIED."""
        mandatory_checks = set(VerificationCheckTypeChoices.values)
        verified_checks = set(
            self.verification_checks.filter(status=CheckStatusChoices.VERIFIED).values_list(
                "check_type", flat=True
            )
        )
        return mandatory_checks.issubset(verified_checks)

    @property
    def verification_summary(self) -> Dict[str, Any]:
        """Provides an aggregated verification status payload."""
        checks = list(self.verification_checks.all())
        total = len(VerificationCheckTypeChoices.values)
        verified = sum(1 for c in checks if c.status == CheckStatusChoices.VERIFIED)
        flagged = sum(1 for c in checks if c.status == CheckStatusChoices.FLAGGED)
        rejected = sum(1 for c in checks if c.status == CheckStatusChoices.REJECTED)
        pending = sum(1 for c in checks if c.status == CheckStatusChoices.PENDING)

        return {
            "total_mandatory_checks": total,
            "verified_count": verified,
            "flagged_count": flagged,
            "rejected_count": rejected,
            "pending_count": pending,
            "is_all_verified": self.is_all_checks_verified,
        }


class JobVerificationCheck(TimeStampedModel):
    """Independently recorded verification checkpoint covering one of the 5 mandatory gates."""

    job = models.ForeignKey(
        JobRequirement,
        on_delete=models.CASCADE,
        related_name="verification_checks",
        db_index=True,
    )
    check_type = models.CharField(
        max_length=32,
        choices=VerificationCheckTypeChoices.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=32,
        choices=CheckStatusChoices.choices,
        default=CheckStatusChoices.PENDING,
        db_index=True,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_job_checks",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Detailed verifier observations, reasoning, and discrepancy details",
    )
    evidence_reference = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Evidence reference (e.g., CIN/GST number, past batch offer letter link, salary survey link)",
    )
    requires_reverification = models.BooleanField(
        default=False,
        help_text="Flagged True when a material field of the job is modified after verification",
    )
    invalidation_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason why this check was invalidated and requires re-verification",
    )

    class Meta:
        db_table = "jobs_verification_check"
        constraints = [
            models.UniqueConstraint(
                fields=["job", "check_type"],
                name="unique_job_verification_check_type",
            )
        ]
        indexes = [
            models.Index(fields=["job", "status"]),
        ]
        verbose_name = "Job Verification Check"
        verbose_name_plural = "Job Verification Checks"

    def __str__(self) -> str:
        return f"{self.job.title} - {self.check_type} ({self.status})"


class JobWorkflowHistory(models.Model):
    """Append-only audit trail recording every state transition and review decision."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        JobRequirement,
        on_delete=models.CASCADE,
        related_name="workflow_history",
        db_index=True,
    )
    from_status = models.CharField(max_length=32)
    to_status = models.CharField(max_length=32)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_workflow_actions",
    )
    action = models.CharField(max_length=64, help_text="e.g. SUBMIT, VERIFY_CHECK, REQUEST_CHANGES, APPROVE, REJECT, AMEND")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "jobs_workflow_history"
        ordering = ["-created_at"]
        verbose_name = "Job Workflow History"
        verbose_name_plural = "Job Workflow Histories"

    def __str__(self) -> str:
        return f"{self.job.title}: {self.from_status} -> {self.to_status} by {self.actor} ({self.action})"

