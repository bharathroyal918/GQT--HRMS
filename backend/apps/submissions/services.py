"""Domain Services and Step 24-28 Candidate Submission Dispatch (MOD-007)."""
import hashlib
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.jobs.models import JobRequirement
from apps.students.models import StudentProfile, StudentResume
from apps.preparation.models import ReadinessCertification
from apps.submissions.models import (
    SubmissionPackage,
    SubmissionItem,
    DispatchLog,
    SubmissionStatusChoices,
)


def generate_submission_code(job: JobRequirement) -> str:
    """Generate sequential unique package code (e.g. SUB-2026-001)."""
    current_year = timezone.now().year
    count = SubmissionPackage.objects.filter(created_at__year=current_year).count() + 1
    return f"SUB-{current_year}-{count:03d}"


@transaction.atomic
def create_submission_package(
    *,
    job: JobRequirement,
    title: str,
    user: User,
    notes: str = "",
) -> SubmissionPackage:
    """Create a new candidate submission package draft."""
    code = generate_submission_code(job)
    package = SubmissionPackage.objects.create(
        job=job,
        package_code=code,
        title=title.strip(),
        created_by=user,
        notes=notes.strip(),
        status=SubmissionStatusChoices.DRAFT,
    )

    AuditLog.objects.create(
        user=user,
        action="SUBMISSION_PACKAGE_CREATED",
        resource_type="SubmissionPackage",
        resource_id=str(package.id),
        changes={"code": code, "job": job.title},
    )

    return package


def add_candidate_to_package(
    *,
    package: SubmissionPackage,
    student: StudentProfile,
    user: User,
) -> SubmissionItem:
    """Attach certified candidate to submission package (strictly enforces Step 23 Gate)."""
    if package.status not in (SubmissionStatusChoices.DRAFT, SubmissionStatusChoices.READY_FOR_REVIEW):
        raise ValidationError("Cannot modify candidates in an approved or dispatched submission package.")

    # Step 23 Hard Gate Check
    is_certified = ReadinessCertification.objects.filter(
        student=student,
        job=package.job,
        is_certified=True,
    ).exists()

    if not is_certified:
        raise ValidationError(
            f"Candidate {student.roll_number} cannot be added without active Step 23 Placement Readiness Certification."
        )

    # Fetch latest verified resume version
    latest_verified_resume = (
        StudentResume.objects.filter(student=student, is_verified=True).order_by("-version").first()
    )
    resume_ver = latest_verified_resume.version if latest_verified_resume else 1

    item, _ = SubmissionItem.objects.update_or_create(
        package=package,
        student=student,
        defaults={"resume_version": resume_ver},
    )

    return item


@transaction.atomic
def approve_submission_package(
    *,
    package: SubmissionPackage,
    user: User,
) -> SubmissionPackage:
    """Placement Head approval and cryptographic roster hash calculation."""
    if package.items.count() == 0:
        raise ValidationError("Cannot approve an empty candidate submission package.")

    # Calculate SHA-256 hash of candidate rolls for tamper-evidence
    rolls = list(package.items.values_list("student__roll_number", flat=True).order_by("student__roll_number"))
    roster_manifest = f"{package.package_code}:{','.join(rolls)}"
    package.roster_hash = hashlib.sha256(roster_manifest.encode("utf-8")).hexdigest()

    package.status = SubmissionStatusChoices.APPROVED
    package.approved_by = user
    package.approved_at = timezone.now()
    package.save()

    AuditLog.objects.create(
        user=user,
        action="SUBMISSION_PACKAGE_APPROVED",
        resource_type="SubmissionPackage",
        resource_id=str(package.id),
        changes={"roster_hash": package.roster_hash, "candidates_count": len(rolls)},
    )

    return package


@transaction.atomic
def dispatch_submission_package(
    *,
    package: SubmissionPackage,
    recipient_email: str,
    recipient_name: str,
    user: User,
    notes: str = "",
) -> DispatchLog:
    """Execute profile dispatch to corporate partner HR contact."""
    if package.status != SubmissionStatusChoices.APPROVED:
        raise ValidationError("Only approved submission packages can be dispatched to corporate recruiters.")

    dispatch_log = DispatchLog.objects.create(
        package=package,
        recipient_email=recipient_email.strip(),
        recipient_name=recipient_name.strip(),
        dispatched_by=user,
        notes=notes.strip(),
    )

    package.status = SubmissionStatusChoices.DISPATCHED
    package.dispatched_at = timezone.now()
    package.save()

    AuditLog.objects.create(
        user=user,
        action="PROFILES_DISPATCHED_TO_HR",
        resource_type="SubmissionPackage",
        resource_id=str(package.id),
        changes={
            "recipient_email": recipient_email,
            "dispatched_at": package.dispatched_at.isoformat(),
        },
    )

    return dispatch_log


def acknowledge_submission_package(
    *,
    package: SubmissionPackage,
    user: User,
    notes: str = "",
) -> SubmissionPackage:
    """Record recruiter receipt and acknowledgement of candidate dispatch."""
    if package.status != SubmissionStatusChoices.DISPATCHED:
        raise ValidationError("Only dispatched packages can be acknowledged.")

    package.status = SubmissionStatusChoices.ACKNOWLEDGED
    package.acknowledged_at = timezone.now()
    if notes:
        package.notes = f"{package.notes}\n[Ack Notes]: {notes}".strip()
    package.save()

    AuditLog.objects.create(
        user=user,
        action="HR_ACKNOWLEDGED_PACKAGE",
        resource_type="SubmissionPackage",
        resource_id=str(package.id),
        changes={"acknowledged_at": package.acknowledged_at.isoformat()},
    )

    return package

