"""Transactional Business Service Layer for Recruitment Creative Studio.

Enforces:
1. Strict Segregation of Duties (SoD): uploader cannot approve their own version.
2. 4-point design compliance check validation prior to sign-off.
3. Cryptographic integrity with SHA-256 and deep magic-byte inspection.
4. Row locking with select_for_update() to prevent race conditions.
5. Immutability and audit logging for every lifecycle event.
"""
import hashlib
import os
import re
from typing import Any, Dict, List, Optional
from uuid import UUID
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User, RoleCatalog
from apps.core.models import AuditLog
from apps.core.middleware import get_current_correlation_id
from apps.crm.models import Company
from apps.jobs.models import JobRequirement
from apps.creatives.models import (
    CreativeRequest,
    CreativeAssetVersion,
    DesignComplianceCheck,
    CreativeWorkflowHistory,
    CreativeStatusChoices,
    CreativeTypeChoices,
    AspectRatioChoices,
    DeliverableFormatChoices,
    CreativePriorityChoices,
    VersionStatusChoices,
    ComplianceCheckTypeChoices,
    ComplianceCheckStatusChoices,
)

MAX_UPLOAD_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB

PERMITTED_MAGIC_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"RIFF", "image/webp"),  # WEBP has RIFF at start and WEBP at byte 8
    (b"%PDF-", "application/pdf"),
]


def generate_request_code() -> str:
    """Generate sequential atomic requisition code: CR-YYYY-NNNN."""
    year = timezone.now().strftime("%Y")
    prefix = f"CR-{year}-"
    latest = (
        CreativeRequest.objects.filter(request_code__startswith=prefix)
        .order_by("-request_code")
        .values_list("request_code", flat=True)
        .first()
    )
    if latest:
        try:
            seq_part = latest.split("-")[-1]
            next_num = int(seq_part) + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1
    return f"{prefix}{next_num:04d}"


def inspect_file_security(uploaded_file: UploadedFile) -> tuple[str, str]:
    """Validate file size, extension, magic byte header, and calculate SHA-256 hash.

    Returns:
        tuple[mime_type, sha256_hash]
    """
    if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(
            f"File size exceeds maximum permitted limit of 15MB (got {uploaded_file.size / (1024 * 1024):.2f}MB)."
        )

    # Sanitize and validate filename extension
    filename = uploaded_file.name or ""
    sanitized_name = os.path.basename(filename).strip()
    if not sanitized_name:
        raise ValidationError("Invalid filename.")

    _, ext = os.path.splitext(sanitized_name)
    ext_lower = ext.lower()
    allowed_exts = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
    if ext_lower not in allowed_exts:
        raise ValidationError(
            f"File extension '{ext}' is not permitted. Permitted formats: PNG, JPG, WEBP, PDF."
        )

    # Read leading bytes for magic signature inspection
    initial_pos = uploaded_file.tell()
    uploaded_file.seek(0)
    header = uploaded_file.read(32)
    uploaded_file.seek(0)

    matched_mime = None
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        matched_mime = "image/png"
    elif header.startswith(b"\xff\xd8\xff"):
        matched_mime = "image/jpeg"
    elif header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP":
        matched_mime = "image/webp"
    elif header.startswith(b"%PDF-"):
        matched_mime = "application/pdf"

    if not matched_mime:
        raise ValidationError(
            "File header signature does not match permitted image or PDF formats. Executable or disguised files are strictly rejected."
        )

    # Calculate SHA-256 hash across full file
    hasher = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        hasher.update(chunk)
    uploaded_file.seek(initial_pos)

    return matched_mime, hasher.hexdigest()


@transaction.atomic
def create_creative_request(
    user: User,
    *,
    title: str,
    brief: str,
    creative_type: str = CreativeTypeChoices.JOB_FLYER,
    aspect_ratio: str = AspectRatioChoices.SQUARE,
    deliverable_format: str = DeliverableFormatChoices.PNG,
    priority: str = CreativePriorityChoices.MEDIUM,
    target_completion_date: Optional[Any] = None,
    job_requirement_id: Optional[UUID | str] = None,
    company_id: Optional[UUID | str] = None,
) -> CreativeRequest:
    """Create a new recruitment creative marketing requisition in DRAFT status."""
    if not title.strip():
        raise ValidationError({"title": "Requisition title cannot be blank."})
    if not brief.strip():
        raise ValidationError({"brief": "Creative brief instructions cannot be blank."})

    job = None
    if job_requirement_id:
        try:
            job = JobRequirement.objects.get(id=job_requirement_id)
        except JobRequirement.DoesNotExist:
            raise ValidationError({"job_requirement": "Referenced Job Requirement does not exist."})

    company = None
    if company_id:
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            raise ValidationError({"company": "Referenced Company does not exist."})
    elif job and job.company:
        company = job.company

    request_code = generate_request_code()

    req = CreativeRequest.objects.create(
        request_code=request_code,
        title=title.strip(),
        creative_type=creative_type,
        aspect_ratio=aspect_ratio,
        deliverable_format=deliverable_format,
        brief=brief.strip(),
        priority=priority,
        target_completion_date=target_completion_date,
        job_requirement=job,
        company=company,
        created_by=user,
        status=CreativeStatusChoices.DRAFT,
    )

    CreativeWorkflowHistory.objects.create(
        request=req,
        from_status="",
        to_status=CreativeStatusChoices.DRAFT,
        actor=user,
        action="CREATE_REQUISITION",
        notes=f"Requisition created in Draft by {user.email}.",
    )

    AuditLog.objects.create(
        user=user,
        action="CREATIVE_REQUEST_CREATED",
        resource_type="creatives.CreativeRequest",
        resource_id=str(req.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "request_code": req.request_code,
            "title": req.title,
            "creative_type": req.creative_type,
            "priority": req.priority,
        },
    )

    return req


@transaction.atomic
def update_creative_request(
    user: User,
    request_id: UUID | str,
    *,
    title: Optional[str] = None,
    brief: Optional[str] = None,
    creative_type: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    deliverable_format: Optional[str] = None,
    priority: Optional[str] = None,
    target_completion_date: Optional[Any] = None,
) -> CreativeRequest:
    """Update requisition brief and specifications in DRAFT or SUBMITTED status."""
    req = CreativeRequest.objects.select_for_update().get(id=request_id)

    if req.status in [
        CreativeStatusChoices.APPROVED,
        CreativeStatusChoices.READY_FOR_HANDOFF,
        CreativeStatusChoices.CANCELLED,
    ]:
        raise ValidationError(
            f"Requisition cannot be modified while in locked status '{req.status}'."
        )

    changes: Dict[str, Any] = {}
    if title is not None and title.strip():
        req.title = title.strip()
        changes["title"] = req.title
    if brief is not None and brief.strip():
        req.brief = brief.strip()
        changes["brief"] = req.brief
    if creative_type is not None:
        req.creative_type = creative_type
        changes["creative_type"] = req.creative_type
    if aspect_ratio is not None:
        req.aspect_ratio = aspect_ratio
        changes["aspect_ratio"] = req.aspect_ratio
    if deliverable_format is not None:
        req.deliverable_format = deliverable_format
        changes["deliverable_format"] = req.deliverable_format
    if priority is not None:
        req.priority = priority
        changes["priority"] = req.priority
    if target_completion_date is not None:
        req.target_completion_date = target_completion_date
        changes["target_completion_date"] = str(req.target_completion_date)

    req.save()

    AuditLog.objects.create(
        user=user,
        action="CREATIVE_REQUEST_UPDATED",
        resource_type="creatives.CreativeRequest",
        resource_id=str(req.id),
        correlation_id=get_current_correlation_id(),
        changes=changes,
    )

    return req


@transaction.atomic
def submit_creative_request(user: User, request_id: UUID | str) -> CreativeRequest:
    """Submit a draft requisition for design triage and assignment."""
    req = CreativeRequest.objects.select_for_update().get(id=request_id)

    if req.status != CreativeStatusChoices.DRAFT:
        raise ValidationError(
            f"Only requisitions in DRAFT status can be submitted (current: {req.status})."
        )

    old_status = req.status
    req.status = CreativeStatusChoices.SUBMITTED
    req.save(update_fields=["status", "updated_at"])

    CreativeWorkflowHistory.objects.create(
        request=req,
        from_status=old_status,
        to_status=req.status,
        actor=user,
        action="SUBMIT_FOR_TRIAGE",
        notes=f"Requisition submitted by {user.email} for designer assignment.",
    )

    AuditLog.objects.create(
        user=user,
        action="CREATIVE_REQUEST_SUBMITTED",
        resource_type="creatives.CreativeRequest",
        resource_id=str(req.id),
        correlation_id=get_current_correlation_id(),
        changes={"from_status": old_status, "to_status": req.status},
    )

    return req


@transaction.atomic
def triage_and_assign_request(
    user: User,
    request_id: UUID | str,
    *,
    assigned_designer_id: UUID | str,
    priority: Optional[str] = None,
    notes: Optional[str] = None,
) -> CreativeRequest:
    """Assign requisition to a graphic designer and set to ASSIGNED status."""
    req = CreativeRequest.objects.select_for_update().get(id=request_id)

    if req.status in [
        CreativeStatusChoices.APPROVED,
        CreativeStatusChoices.READY_FOR_HANDOFF,
        CreativeStatusChoices.CANCELLED,
    ]:
        raise ValidationError(
            f"Cannot assign designer to requisition in '{req.status}' status."
        )

    try:
        designer = User.objects.get(id=assigned_designer_id)
    except User.DoesNotExist:
        raise ValidationError({"assigned_designer_id": "Selected designer user does not exist."})

    old_status = req.status
    req.assigned_designer = designer
    req.status = CreativeStatusChoices.ASSIGNED
    if priority:
        req.priority = priority

    req.save(update_fields=["assigned_designer", "status", "priority", "updated_at"])

    CreativeWorkflowHistory.objects.create(
        request=req,
        from_status=old_status,
        to_status=req.status,
        actor=user,
        action="ASSIGN_DESIGNER",
        notes=f"Assigned to {designer.email} by {user.email}. {notes or ''}".strip(),
    )

    AuditLog.objects.create(
        user=user,
        action="CREATIVE_DESIGNER_ASSIGNED",
        resource_type="creatives.CreativeRequest",
        resource_id=str(req.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "assigned_designer_id": str(designer.id),
            "assigned_designer_email": designer.email,
            "status": req.status,
            "priority": req.priority,
        },
    )

    return req


@transaction.atomic
def upload_asset_version(
    user: User,
    request_id: UUID | str,
    *,
    uploaded_file: UploadedFile,
    designer_notes: Optional[str] = None,
) -> CreativeAssetVersion:
    """Upload a new design asset deliverable version with security checks.

    Enforces file size limit, magic bytes, SHA-256 digest, and initializes
    the 4 mandatory design compliance checks in PENDING status.
    """
    req = CreativeRequest.objects.select_for_update().get(id=request_id)

    if req.status in [
        CreativeStatusChoices.APPROVED,
        CreativeStatusChoices.READY_FOR_HANDOFF,
        CreativeStatusChoices.CANCELLED,
    ]:
        raise ValidationError(
            f"Cannot upload asset version for requisition in '{req.status}' status."
        )

    # Security inspection
    mime_type, sha256_hash = inspect_file_security(uploaded_file)
    original_name = os.path.basename(uploaded_file.name or "asset")

    # Determine sequential version number while parent lock is held
    current_max = (
        CreativeAssetVersion.objects.filter(request=req)
        .order_by("-version_number")
        .values_list("version_number", flat=True)
        .first()
        or 0
    )
    new_version_num = current_max + 1

    try:
        with transaction.atomic():
            version = CreativeAssetVersion.objects.create(
                request=req,
                version_number=new_version_num,
                file=uploaded_file,
                original_filename=original_name,
                file_size_bytes=uploaded_file.size,
                mime_type=mime_type,
                sha256_hash=sha256_hash,
                designer_notes=(designer_notes or "").strip(),
                uploader=user,
                status=VersionStatusChoices.SUBMITTED_FOR_REVIEW,
            )
    except IntegrityError as exc:
        raise ValidationError(
            {"detail": "A version creation conflict occurred for this requisition. Please retry."}
        ) from exc

    # Initialize all 4 mandatory compliance checks in PENDING status
    for check_type in ComplianceCheckTypeChoices.values:
        DesignComplianceCheck.objects.create(
            asset_version=version,
            check_type=check_type,
            status=ComplianceCheckStatusChoices.PENDING,
        )

    # Update requisition status to IN_REVIEW and link as active candidate
    old_req_status = req.status
    req.status = CreativeStatusChoices.IN_REVIEW
    req.active_version = version
    req.save(update_fields=["status", "active_version", "updated_at"])

    CreativeWorkflowHistory.objects.create(
        request=req,
        from_status=old_req_status,
        to_status=req.status,
        actor=user,
        action="UPLOAD_VERSION",
        notes=f"Version v{new_version_num} ({original_name}) uploaded by {user.email} and submitted for review.",
    )

    AuditLog.objects.create(
        user=user,
        action="CREATIVE_VERSION_UPLOADED",
        resource_type="creatives.CreativeAssetVersion",
        resource_id=str(version.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "request_id": str(req.id),
            "version_number": new_version_num,
            "filename": original_name,
            "sha256_hash": sha256_hash,
            "mime_type": mime_type,
            "file_size_bytes": uploaded_file.size,
        },
    )

    return version


@transaction.atomic
def evaluate_compliance_check(
    user: User,
    version_id: UUID | str,
    check_type: str,
    *,
    status: str,
    notes: Optional[str] = None,
) -> DesignComplianceCheck:
    """Evaluate one of the 4 mandatory compliance checks for an asset version."""
    version = CreativeAssetVersion.objects.select_for_update().get(id=version_id)

    if status not in ComplianceCheckStatusChoices.values:
        raise ValidationError(f"Invalid evaluation status '{status}'.")

    if status == ComplianceCheckStatusChoices.FLAGGED and not (notes and notes.strip()):
        raise ValidationError(
            {"notes": "Evaluation notes are mandatory when flagging a design compliance discrepancy."}
        )

    try:
        check = DesignComplianceCheck.objects.select_for_update().get(
            asset_version=version, check_type=check_type
        )
    except DesignComplianceCheck.DoesNotExist:
        raise ValidationError(f"Check type '{check_type}' does not exist for this version.")

    old_status = check.status
    check.status = status
    check.notes = (notes or "").strip()
    check.verified_by = user
    check.verified_at = timezone.now()
    check.save()

    AuditLog.objects.create(
        user=user,
        action="CREATIVE_CHECK_EVALUATED",
        resource_type="creatives.DesignComplianceCheck",
        resource_id=str(check.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "version_id": str(version.id),
            "check_type": check_type,
            "from_status": old_status,
            "to_status": status,
            "notes": check.notes,
        },
    )

    return check


@transaction.atomic
def approve_asset_version(
    user: User,
    version_id: UUID | str,
    *,
    review_feedback: Optional[str] = None,
) -> CreativeAssetVersion:
    """Authorize and sign off an asset version.

    Strictly enforces:
    1. Segregation of Duties (SoD): uploader cannot approve their own version.
    2. All 4 DesignComplianceCheck records must be PASSED.
    """
    version = (
        CreativeAssetVersion.objects.select_for_update()
        .select_related("request", "uploader")
        .get(id=version_id)
    )
    req = CreativeRequest.objects.select_for_update().get(id=version.request_id)

    # SoD Check: uploader cannot approve their own version (no superuser exemption)
    if version.uploader_id == user.id:
        raise ValidationError(
            "Segregation of duties violation: Designers cannot self-approve their own asset submissions."
        )

    # Compliance Gate: All 4 checks must be PASSED
    checks = list(version.compliance_checks.all())
    if len(checks) < 4:
        raise ValidationError("Version compliance checks are incomplete.")

    unpassed = [
        c.get_check_type_display()
        for c in checks
        if c.status != ComplianceCheckStatusChoices.PASSED
    ]
    if unpassed:
        raise ValidationError(
            f"All 4 design compliance checks must be passed before final asset approval. Unpassed: {', '.join(unpassed)}."
        )

    old_version_status = version.status
    version.status = VersionStatusChoices.APPROVED
    version.reviewed_by = user
    version.reviewed_at = timezone.now()
    version.review_feedback = (review_feedback or "Approved for release.").strip()
    version.save()

    # Mark prior versions as SUPERSEDED
    CreativeAssetVersion.objects.filter(
        request=req,
        version_number__lt=version.version_number,
    ).exclude(status=VersionStatusChoices.SUPERSEDED).update(status=VersionStatusChoices.SUPERSEDED)

    # Advance Requisition status to APPROVED and establish active_version
    old_req_status = req.status
    req.status = CreativeStatusChoices.APPROVED
    req.active_version = version
    req.save(update_fields=["status", "active_version", "updated_at"])

    CreativeWorkflowHistory.objects.create(
        request=req,
        from_status=old_req_status,
        to_status=req.status,
        actor=user,
        action="APPROVE_VERSION",
        notes=f"Version v{version.version_number} approved by {user.email}. {version.review_feedback}",
    )

    AuditLog.objects.create(
        user=user,
        action="CREATIVE_VERSION_APPROVED",
        resource_type="creatives.CreativeAssetVersion",
        resource_id=str(version.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "request_id": str(req.id),
            "version_number": version.version_number,
            "reviewed_by": user.email,
            "feedback": version.review_feedback,
        },
    )

    return version


@transaction.atomic
def request_changes_on_version(
    user: User,
    version_id: UUID | str,
    *,
    review_feedback: str,
) -> CreativeAssetVersion:
    """Request revisions from the designer on an asset version."""
    if not review_feedback or not review_feedback.strip():
        raise ValidationError(
            {"review_feedback": "Detailed reviewer feedback explaining requested adjustments is required."}
        )

    version = (
        CreativeAssetVersion.objects.select_for_update()
        .select_related("request")
        .get(id=version_id)
    )
    req = CreativeRequest.objects.select_for_update().get(id=version.request_id)

    version.status = VersionStatusChoices.CHANGES_REQUESTED
    version.reviewed_by = user
    version.reviewed_at = timezone.now()
    version.review_feedback = review_feedback.strip()
    version.save()

    old_req_status = req.status
    req.status = CreativeStatusChoices.CHANGES_REQUESTED
    req.save(update_fields=["status", "updated_at"])

    CreativeWorkflowHistory.objects.create(
        request=req,
        from_status=old_req_status,
        to_status=req.status,
        actor=user,
        action="REQUEST_CHANGES",
        notes=f"Changes requested on v{version.version_number} by {user.email}: {review_feedback.strip()}",
    )

    AuditLog.objects.create(
        user=user,
        action="CREATIVE_CHANGES_REQUESTED",
        resource_type="creatives.CreativeAssetVersion",
        resource_id=str(version.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "request_id": str(req.id),
            "version_number": version.version_number,
            "reviewed_by": user.email,
            "feedback": version.review_feedback,
        },
    )

    return version


@transaction.atomic
def mark_ready_for_handoff(
    user: User,
    request_id: UUID | str,
    *,
    notes: Optional[str] = None,
) -> CreativeRequest:
    """Mark an approved requisition as READY_FOR_HANDOFF for placement drives."""
    req = CreativeRequest.objects.select_for_update().get(id=request_id)

    if req.status != CreativeStatusChoices.APPROVED:
        raise ValidationError(
            f"Only requisitions with an APPROVED asset version can be handed off (current: {req.status})."
        )
    if not req.active_version or req.active_version.status != VersionStatusChoices.APPROVED:
        raise ValidationError("Requisition does not possess a signed-off active asset version.")

    old_status = req.status
    req.status = CreativeStatusChoices.READY_FOR_HANDOFF
    req.save(update_fields=["status", "updated_at"])

    CreativeWorkflowHistory.objects.create(
        request=req,
        from_status=old_status,
        to_status=req.status,
        actor=user,
        action="MARK_READY_FOR_HANDOFF",
        notes=f"Marked ready for campus drive collateral by {user.email}. {notes or ''}".strip(),
    )

    AuditLog.objects.create(
        user=user,
        action="CREATIVE_READY_FOR_HANDOFF",
        resource_type="creatives.CreativeRequest",
        resource_id=str(req.id),
        correlation_id=get_current_correlation_id(),
        changes={"from_status": old_status, "to_status": req.status},
    )

    return req


@transaction.atomic
def cancel_creative_request(
    user: User,
    request_id: UUID | str,
    *,
    cancellation_reason: str,
) -> CreativeRequest:
    """Cancel a requisition with mandatory reason documentation."""
    if not cancellation_reason or not cancellation_reason.strip():
        raise ValidationError(
            {"cancellation_reason": "A documented cancellation reason is required."}
        )

    req = CreativeRequest.objects.select_for_update().get(id=request_id)

    if req.status in [
        CreativeStatusChoices.APPROVED,
        CreativeStatusChoices.READY_FOR_HANDOFF,
    ]:
        raise ValidationError(
            f"Approved or handed-off requisitions cannot be cancelled directly."
        )

    old_status = req.status
    req.status = CreativeStatusChoices.CANCELLED
    req.cancellation_reason = cancellation_reason.strip()
    req.save(update_fields=["status", "cancellation_reason", "updated_at"])

    CreativeWorkflowHistory.objects.create(
        request=req,
        from_status=old_status,
        to_status=req.status,
        actor=user,
        action="CANCEL_REQUISITION",
        notes=f"Cancelled by {user.email}. Reason: {cancellation_reason.strip()}",
    )

    AuditLog.objects.create(
        user=user,
        action="CREATIVE_REQUEST_CANCELLED",
        resource_type="creatives.CreativeRequest",
        resource_id=str(req.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "from_status": old_status,
            "to_status": req.status,
            "reason": cancellation_reason.strip(),
        },
    )

    return req

