"""Domain Persistence Models for GQT Recruitment Creative Studio.

Manages recruitment creative requisitions, sequential deliverable asset versioning,
4-point brand and policy compliance checks, and workflow history.
"""
import os
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


def creative_upload_path(instance: "CreativeAssetVersion", filename: str) -> str:
    """Generate isolated private file storage path partitioned by year and request ID."""
    year = timezone.now().strftime("%Y")
    request_id = str(instance.request_id) if instance.request_id else "unassigned"
    version_id = str(instance.id or uuid.uuid4())
    _, ext = os.path.splitext(filename)
    safe_filename = f"{version_id}{ext.lower()}"
    return os.path.join("creatives", year, request_id, safe_filename)


class CreativeStatusChoices(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted for Triage"
    ASSIGNED = "ASSIGNED", "Assigned to Designer"
    IN_DESIGN = "IN_DESIGN", "In Design"
    IN_REVIEW = "IN_REVIEW", "In Review"
    CHANGES_REQUESTED = "CHANGES_REQUESTED", "Changes Requested"
    APPROVED = "APPROVED", "Approved"
    READY_FOR_HANDOFF = "READY_FOR_HANDOFF", "Ready for Handoff"
    CANCELLED = "CANCELLED", "Cancelled"


class CreativeTypeChoices(models.TextChoices):
    JOB_FLYER = "JOB_FLYER", "Job Opening Flyer"
    WHATSAPP_BANNER = "WHATSAPP_BANNER", "WhatsApp Banner"
    INSTAGRAM_POST = "INSTAGRAM_POST", "Instagram Post (1:1)"
    LINKEDIN_BANNER = "LINKEDIN_BANNER", "LinkedIn Post (16:9)"
    EMAIL_HEADER = "EMAIL_HEADER", "Email Header Graphic"
    CAMPUS_POSTER = "CAMPUS_POSTER", "Campus Noticeboard Poster (A4)"
    CUSTOM = "CUSTOM", "Custom Marketing Asset"


class AspectRatioChoices(models.TextChoices):
    SQUARE = "1:1", "1:1 Square"
    LANDSCAPE = "16:9", "16:9 Landscape"
    PORTRAIT = "9:16", "9:16 Story / Reel"
    BANNER_4_5 = "4:5", "4:5 Social Banner"
    A4_PRINT = "A4_PORTRAIT", "A4 Print Format"
    CUSTOM = "CUSTOM", "Custom Aspect Ratio"


class DeliverableFormatChoices(models.TextChoices):
    PNG = "PNG", "PNG Image"
    JPEG = "JPEG", "JPEG Image"
    WEBP = "WEBP", "WebP Image"
    PDF = "PDF", "Print-Ready PDF"
    MULTI_FORMAT = "MULTI_FORMAT", "Multi-Format Package"


class CreativePriorityChoices(models.TextChoices):
    LOW = "LOW", "Low Priority"
    MEDIUM = "MEDIUM", "Medium Priority"
    HIGH = "HIGH", "High Priority"
    URGENT = "URGENT", "Urgent / Fast-Track"


class VersionStatusChoices(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED_FOR_REVIEW = "SUBMITTED_FOR_REVIEW", "Submitted for Review"
    CHANGES_REQUESTED = "CHANGES_REQUESTED", "Changes Requested"
    APPROVED = "APPROVED", "Approved"
    SUPERSEDED = "SUPERSEDED", "Superseded"


class ComplianceCheckTypeChoices(models.TextChoices):
    FLYER_TEXT_ACCURACY = (
        "FLYER_TEXT_ACCURACY",
        "Job Title, CTC & Eligibility Accuracy",
    )
    BRAND_ASSETS_COMPLIANCE = (
        "BRAND_ASSETS_COMPLIANCE",
        "Official GQT & Company Brand Assets",
    )
    QR_CODE_INTEGRITY = (
        "QR_CODE_INTEGRITY",
        "QR Code Routing & Link Validation",
    )
    CONTACT_DISCLOSURE = (
        "CONTACT_DISCLOSURE",
        "Recruiter Contact & Zero-Fee Placement Policy",
    )


class ComplianceCheckStatusChoices(models.TextChoices):
    PENDING = "PENDING", "Pending Review"
    PASSED = "PASSED", "Passed Compliance"
    FLAGGED = "FLAGGED", "Flagged for Revision"


class CreativeRequest(models.Model):
    """Recruitment creative marketing requisition."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_code = models.CharField(
        max_length=32, unique=True, db_index=True, editable=False
    )
    title = models.CharField(max_length=255)
    creative_type = models.CharField(
        max_length=32,
        choices=CreativeTypeChoices.choices,
        default=CreativeTypeChoices.JOB_FLYER,
    )
    aspect_ratio = models.CharField(
        max_length=32,
        choices=AspectRatioChoices.choices,
        default=AspectRatioChoices.SQUARE,
    )
    deliverable_format = models.CharField(
        max_length=32,
        choices=DeliverableFormatChoices.choices,
        default=DeliverableFormatChoices.PNG,
    )
    brief = models.TextField(
        help_text="Detailed creative instructions, role highlights, candidate requirements, and visual specifications."
    )
    priority = models.CharField(
        max_length=16,
        choices=CreativePriorityChoices.choices,
        default=CreativePriorityChoices.MEDIUM,
    )
    status = models.CharField(
        max_length=32,
        choices=CreativeStatusChoices.choices,
        default=CreativeStatusChoices.DRAFT,
        db_index=True,
    )

    # Relationships
    job_requirement = models.ForeignKey(
        "jobs.JobRequirement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="creative_requests",
    )
    company = models.ForeignKey(
        "crm.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="creative_requests",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_creative_requests",
    )
    assigned_designer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_creative_requests",
    )
    active_version = models.ForeignKey(
        "CreativeAssetVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    target_completion_date = models.DateField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Creative Requisition"
        verbose_name_plural = "Creative Requisitions"

    def __str__(self) -> str:
        return f"{self.request_code} — {self.title} ({self.get_status_display()})"


class CreativeAssetVersion(models.Model):
    """Sequential deliverable asset submission for a creative request."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        CreativeRequest, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    file = models.FileField(upload_to=creative_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size_bytes = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    sha256_hash = models.CharField(max_length=64, db_index=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)

    designer_notes = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=VersionStatusChoices.choices,
        default=VersionStatusChoices.DRAFT,
        db_index=True,
    )

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_creative_versions",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_creative_versions",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_feedback = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["request", "version_number"],
                name="unique_version_per_creative_request",
            )
        ]
        verbose_name = "Creative Asset Version"
        verbose_name_plural = "Creative Asset Versions"

    def __str__(self) -> str:
        return f"{self.request.request_code} v{self.version_number} ({self.get_status_display()})"


class DesignComplianceCheck(models.Model):
    """4-point design and brand policy compliance check per asset version."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset_version = models.ForeignKey(
        CreativeAssetVersion,
        on_delete=models.CASCADE,
        related_name="compliance_checks",
    )
    check_type = models.CharField(
        max_length=32, choices=ComplianceCheckTypeChoices.choices
    )
    status = models.CharField(
        max_length=16,
        choices=ComplianceCheckStatusChoices.choices,
        default=ComplianceCheckStatusChoices.PENDING,
    )
    notes = models.TextField(blank=True, default="")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_creative_checks",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["check_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["asset_version", "check_type"],
                name="unique_check_type_per_asset_version",
            )
        ]
        verbose_name = "Design Compliance Check"
        verbose_name_plural = "Design Compliance Checks"

    def __str__(self) -> str:
        return f"{self.asset_version.request.request_code} v{self.asset_version.version_number} - {self.get_check_type_display()} [{self.status}]"


class CreativeWorkflowHistory(models.Model):
    """Immutable audit trail of requisition lifecycle and assignment transitions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        CreativeRequest, on_delete=models.CASCADE, related_name="history"
    )
    from_status = models.CharField(max_length=32, blank=True, default="")
    to_status = models.CharField(max_length=32)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=64)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Creative Workflow History"
        verbose_name_plural = "Creative Workflow Histories"

    def __str__(self) -> str:
        return f"{self.request.request_code}: {self.from_status} -> {self.to_status} by {self.actor}"

