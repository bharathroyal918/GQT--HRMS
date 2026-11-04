"""Transactional Service Layer for Job Requirements, Verification, and Approvals.

Enforces Segregation of Duties (SoD), 5-point verification gates, row locking,
material field change invalidation, and comprehensive audit logging.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User, RoleCatalog
from apps.core.models import AuditLog
from apps.core.middleware import get_current_correlation_id
from apps.crm.models import Company
from apps.jobs.models import (
    JobRequirement,
    JobVerificationCheck,
    JobWorkflowHistory,
    JobStatusChoices,
    VerificationCheckTypeChoices,
    CheckStatusChoices,
)


# Material field mappings to the verification checks they affect
MATERIAL_FIELDS_MAPPING = {
    "ELIGIBILITY": [
        "min_cgpa",
        "min_percentage",
        "eligible_batches",
        "eligible_branches",
        "max_backlogs_allowed",
    ],
    "SALARY_AUTHENTICITY": [
        "min_ctc_lpa",
        "max_ctc_lpa",
        "stipend_amount",
        "salary_details",
    ],
    "COMPANY_AUTHENTICITY": [
        "company",
    ],
    "INTERVIEW_PROCESS": [
        "interview_rounds",
        "interview_process_notes",
        "has_bond",
        "bond_duration_months",
        "bond_details",
    ],
    "REGISTRATION_DEADLINE": [
        "registration_deadline",
        "interview_date",
    ],
}


@transaction.atomic
def create_job_requirement(
    *,
    company: Company,
    title: str,
    description: str,
    min_ctc_lpa: Decimal,
    max_ctc_lpa: Decimal,
    registration_deadline: timezone.datetime,
    user: User,
    role_category: str = "",
    required_skills: Optional[List[str]] = None,
    min_cgpa: Optional[Decimal] = None,
    min_percentage: Optional[Decimal] = None,
    eligible_batches: Optional[List[str]] = None,
    eligible_branches: Optional[List[str]] = None,
    max_backlogs_allowed: int = 0,
    stipend_amount: Optional[Decimal] = None,
    salary_details: str = "",
    job_location: str = "",
    work_arrangement: str = "",
    has_bond: bool = False,
    bond_duration_months: Optional[int] = None,
    bond_details: str = "",
    interview_rounds: Optional[List[Dict[str, Any]]] = None,
    interview_process_notes: str = "",
    interview_date: Optional[timezone.datetime] = None,
    vacancies_count: Optional[int] = None,
) -> JobRequirement:
    """Creates a new JobRequirement draft and initializes all 5 mandatory verification checks."""
    if registration_deadline <= timezone.now():
        raise ValidationError({"registration_deadline": "Registration deadline must be a future timestamp."})

    job = JobRequirement(
        company=company,
        title=title.strip(),
        description=description.strip(),
        min_ctc_lpa=min_ctc_lpa,
        max_ctc_lpa=max_ctc_lpa,
        registration_deadline=registration_deadline,
        role_category=role_category or JobRequirement._meta.get_field("role_category").default,
        required_skills=required_skills or [],
        min_cgpa=min_cgpa,
        min_percentage=min_percentage,
        eligible_batches=eligible_batches or [],
        eligible_branches=eligible_branches or [],
        max_backlogs_allowed=max_backlogs_allowed,
        stipend_amount=stipend_amount,
        salary_details=salary_details.strip(),
        job_location=job_location.strip(),
        work_arrangement=work_arrangement or JobRequirement._meta.get_field("work_arrangement").default,
        has_bond=has_bond,
        bond_duration_months=bond_duration_months,
        bond_details=bond_details.strip(),
        interview_rounds=interview_rounds or [],
        interview_process_notes=interview_process_notes.strip(),
        interview_date=interview_date,
        vacancies_count=vacancies_count,
        submitted_by=user,
        created_by=user,
        updated_by=user,
        status=JobStatusChoices.DRAFT,
    )
    job.full_clean()
    job.save()

    # Initialize all 5 mandatory checklist gates in PENDING status
    for check_type in VerificationCheckTypeChoices.values:
        JobVerificationCheck.objects.create(
            job=job,
            check_type=check_type,
            status=CheckStatusChoices.PENDING,
        )

    # Workflow History
    JobWorkflowHistory.objects.create(
        job=job,
        from_status="",
        to_status=JobStatusChoices.DRAFT,
        actor=user,
        action="CREATE_DRAFT",
        notes=f"Draft requirement created by {user.email}.",
    )

    # Audit Log
    AuditLog.objects.create(
        user=user,
        action="JOB_REQUIREMENT_CREATED",
        resource_type="jobs.JobRequirement",
        resource_id=str(job.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "title": job.title,
            "company_id": str(company.id),
            "status": job.status,
            "min_ctc_lpa": str(job.min_ctc_lpa),
            "max_ctc_lpa": str(job.max_ctc_lpa),
        },
    )

    return job


@transaction.atomic
def update_job_requirement(
    *,
    job: JobRequirement,
    user: User,
    **fields,
) -> JobRequirement:
    """Updates job fields with material field tracking and check invalidation."""
    locked_job = JobRequirement.objects.select_for_update().get(id=job.id)

    if locked_job.status == JobStatusChoices.APPROVED:
        raise ValidationError("Approved jobs cannot be modified directly. Use authorized amendment workflow.")

    if locked_job.status == JobStatusChoices.REJECTED:
        raise ValidationError("Rejected jobs cannot be modified.")

    changes: Dict[str, Any] = {}
    invalidated_checks: List[str] = []

    # Map of modified material fields to affected check types
    for check_type, material_fields in MATERIAL_FIELDS_MAPPING.items():
        affects_check = False
        for field_name in material_fields:
            if field_name in fields:
                old_val = getattr(locked_job, field_name)
                new_val = fields[field_name]
                if old_val != new_val:
                    affects_check = True
                    break
        if affects_check:
            invalidated_checks.append(check_type)

    # Apply updatable fields
    updatable_fields = [
        "title",
        "description",
        "role_category",
        "required_skills",
        "min_cgpa",
        "min_percentage",
        "eligible_batches",
        "eligible_branches",
        "max_backlogs_allowed",
        "min_ctc_lpa",
        "max_ctc_lpa",
        "stipend_amount",
        "salary_details",
        "job_location",
        "work_arrangement",
        "has_bond",
        "bond_duration_months",
        "bond_details",
        "interview_rounds",
        "interview_process_notes",
        "interview_date",
        "registration_deadline",
        "vacancies_count",
    ]

    for key in updatable_fields:
        if key in fields:
            val = fields[key]
            current_val = getattr(locked_job, key)
            if current_val != val:
                changes[key] = {"old": str(current_val), "new": str(val)}
                setattr(locked_job, key, val)

    if "company" in fields:
        new_company = fields["company"]
        if locked_job.company != new_company:
            changes["company"] = {"old": str(locked_job.company_id), "new": str(new_company.id)}
            locked_job.company = new_company

    locked_job.updated_by = user
    locked_job.full_clean()

    # Invalidate affected verification checks
    if invalidated_checks:
        for c_type in invalidated_checks:
            check_obj = locked_job.verification_checks.filter(check_type=c_type).first()
            if check_obj and check_obj.status == CheckStatusChoices.VERIFIED:
                check_obj.status = CheckStatusChoices.PENDING
                check_obj.requires_reverification = True
                check_obj.invalidation_reason = f"Material field change detected in {c_type} parameters."
                check_obj.save()

        # If job was in PENDING_APPROVAL, drop it back to UNDER_VERIFICATION because checks are no longer 100% verified
        if locked_job.status == JobStatusChoices.PENDING_APPROVAL:
            old_st = locked_job.status
            locked_job.status = JobStatusChoices.UNDER_VERIFICATION
            JobWorkflowHistory.objects.create(
                job=locked_job,
                from_status=old_st,
                to_status=locked_job.status,
                actor=user,
                action="INVALIDATE_CHECKS_ON_EDIT",
                notes=f"Checks {invalidated_checks} invalidated by material edits. Dropped from PENDING_APPROVAL.",
            )

    locked_job.save()

    if changes:
        AuditLog.objects.create(
            user=user,
            action="JOB_REQUIREMENT_UPDATED",
            resource_type="jobs.JobRequirement",
            resource_id=str(locked_job.id),
            correlation_id=get_current_correlation_id(),
            changes=changes,
        )

    return locked_job


@transaction.atomic
def submit_for_verification(
    *,
    job: JobRequirement,
    user: User,
) -> JobRequirement:
    """Submits a draft or changes-requested job for 5-point verification review."""
    locked_job = JobRequirement.objects.select_for_update().get(id=job.id)

    if locked_job.status not in [JobStatusChoices.DRAFT, JobStatusChoices.CHANGES_REQUESTED]:
        raise ValidationError(f"Cannot submit job for verification from '{locked_job.status}' status.")

    if locked_job.registration_deadline <= timezone.now():
        raise ValidationError({"registration_deadline": "Registration deadline has expired. Update deadline before submitting."})

    from_st = locked_job.status
    locked_job.status = JobStatusChoices.PENDING_VERIFICATION
    locked_job.submitted_by = user
    locked_job.updated_by = user
    locked_job.save(update_fields=["status", "submitted_by", "updated_by", "updated_at"])

    JobWorkflowHistory.objects.create(
        job=locked_job,
        from_status=from_st,
        to_status=locked_job.status,
        actor=user,
        action="SUBMIT_FOR_VERIFICATION",
        notes=f"Submitted for verification review by {user.email}.",
    )

    AuditLog.objects.create(
        user=user,
        action="JOB_SUBMITTED_FOR_VERIFICATION",
        resource_type="jobs.JobRequirement",
        resource_id=str(locked_job.id),
        correlation_id=get_current_correlation_id(),
        changes={"from_status": from_st, "to_status": locked_job.status},
    )

    return locked_job


@transaction.atomic
def assign_verifier(
    *,
    job: JobRequirement,
    verifier: User,
    user: User,
) -> JobRequirement:
    """Assigns a staff member to conduct the verification review."""
    locked_job = JobRequirement.objects.select_for_update().get(id=job.id)

    if locked_job.status not in [JobStatusChoices.PENDING_VERIFICATION, JobStatusChoices.UNDER_VERIFICATION]:
        raise ValidationError(f"Cannot assign verifier when job is in '{locked_job.status}' status.")

    from_st = locked_job.status
    locked_job.assigned_verifier = verifier
    locked_job.status = JobStatusChoices.UNDER_VERIFICATION
    locked_job.updated_by = user
    locked_job.save(update_fields=["assigned_verifier", "status", "updated_by", "updated_at"])

    JobWorkflowHistory.objects.create(
        job=locked_job,
        from_status=from_st,
        to_status=locked_job.status,
        actor=user,
        action="ASSIGN_VERIFIER",
        notes=f"Verifier assigned to {verifier.email} by {user.email}.",
    )

    AuditLog.objects.create(
        user=user,
        action="JOB_VERIFIER_ASSIGNED",
        resource_type="jobs.JobRequirement",
        resource_id=str(locked_job.id),
        correlation_id=get_current_correlation_id(),
        changes={"assigned_verifier": str(verifier.id), "status": locked_job.status},
    )

    return locked_job


@transaction.atomic
def update_verification_check(
    *,
    job: JobRequirement,
    check_type: str,
    status: str,
    user: User,
    notes: str = "",
    evidence_reference: str = "",
) -> JobVerificationCheck:
    """Records reviewer evaluation for one of the five mandatory verification checkpoints."""
    locked_job = JobRequirement.objects.select_for_update().get(id=job.id)

    if locked_job.status in [JobStatusChoices.APPROVED, JobStatusChoices.REJECTED]:
        raise ValidationError(f"Cannot update verification checks on a '{locked_job.status}' job.")

    if status in [CheckStatusChoices.FLAGGED, CheckStatusChoices.REJECTED] and not notes.strip():
        raise ValidationError({"notes": "Meaningful reviewer notes are required when flagging or rejecting a check."})

    check = locked_job.verification_checks.select_for_update().filter(check_type=check_type).first()
    if not check:
        raise ValidationError(f"Verification check '{check_type}' does not exist for this job.")

    old_status = check.status
    check.status = status
    check.notes = notes.strip()
    check.evidence_reference = evidence_reference.strip()
    check.verified_by = user
    check.verified_at = timezone.now() if status == CheckStatusChoices.VERIFIED else None
    check.requires_reverification = False
    check.invalidation_reason = ""
    check.save()

    JobWorkflowHistory.objects.create(
        job=locked_job,
        from_status=locked_job.status,
        to_status=locked_job.status,
        actor=user,
        action="UPDATE_CHECK",
        notes=f"Check '{check_type}' updated from {old_status} to {status} by {user.email}.",
    )

    # Automatically advance to PENDING_APPROVAL when all 5 checks reach VERIFIED
    if locked_job.is_all_checks_verified:
        if locked_job.status in [JobStatusChoices.PENDING_VERIFICATION, JobStatusChoices.UNDER_VERIFICATION]:
            old_job_status = locked_job.status
            locked_job.status = JobStatusChoices.PENDING_APPROVAL
            locked_job.save(update_fields=["status", "updated_at"])

            JobWorkflowHistory.objects.create(
                job=locked_job,
                from_status=old_job_status,
                to_status=JobStatusChoices.PENDING_APPROVAL,
                actor=user,
                action="ADVANCE_TO_PENDING_APPROVAL",
                notes="All five mandatory checks VERIFIED. Advanced to pending approval queue.",
            )
    elif locked_job.status == JobStatusChoices.PENDING_APPROVAL and status != CheckStatusChoices.VERIFIED:
        # If any check falls out of VERIFIED, drop back to UNDER_VERIFICATION
        old_job_status = locked_job.status
        locked_job.status = JobStatusChoices.UNDER_VERIFICATION
        locked_job.save(update_fields=["status", "updated_at"])

        JobWorkflowHistory.objects.create(
            job=locked_job,
            from_status=old_job_status,
            to_status=JobStatusChoices.UNDER_VERIFICATION,
            actor=user,
            action="DROP_FROM_PENDING_APPROVAL",
            notes=f"Check '{check_type}' is no longer VERIFIED ({status}). Dropped to under verification.",
        )

    AuditLog.objects.create(
        user=user,
        action="JOB_VERIFICATION_CHECK_UPDATED",
        resource_type="jobs.JobVerificationCheck",
        resource_id=str(check.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "check_type": check_type,
            "old_status": old_status,
            "new_status": status,
            "evidence_reference": check.evidence_reference,
        },
    )

    return check


@transaction.atomic
def request_changes(
    *,
    job: JobRequirement,
    reason: str,
    user: User,
) -> JobRequirement:
    """Returns job to Placement Officer with mandatory feedback."""
    locked_job = JobRequirement.objects.select_for_update().get(id=job.id)

    if not reason.strip():
        raise ValidationError({"reason": "A specific, meaningful reason must be provided when requesting changes."})

    allowed_from_statuses = [
        JobStatusChoices.PENDING_VERIFICATION,
        JobStatusChoices.UNDER_VERIFICATION,
        JobStatusChoices.PENDING_APPROVAL,
    ]
    if locked_job.status not in allowed_from_statuses:
        raise ValidationError(f"Cannot request changes on a job in '{locked_job.status}' status.")

    from_st = locked_job.status
    locked_job.status = JobStatusChoices.CHANGES_REQUESTED
    locked_job.changes_requested_reason = reason.strip()
    locked_job.updated_by = user
    locked_job.save(update_fields=["status", "changes_requested_reason", "updated_by", "updated_at"])

    JobWorkflowHistory.objects.create(
        job=locked_job,
        from_status=from_st,
        to_status=locked_job.status,
        actor=user,
        action="REQUEST_CHANGES",
        notes=reason.strip(),
    )

    AuditLog.objects.create(
        user=user,
        action="JOB_CHANGES_REQUESTED",
        resource_type="jobs.JobRequirement",
        resource_id=str(locked_job.id),
        correlation_id=get_current_correlation_id(),
        changes={"from_status": from_st, "reason": reason.strip()},
    )

    return locked_job


@transaction.atomic
def approve_job(
    *,
    job: JobRequirement,
    user: User,
    notes: str = "",
) -> JobRequirement:
    """Approves a verified JobRequirement. Strictly enforces Segregation of Duties and 5-check completion."""
    locked_job = JobRequirement.objects.select_for_update().get(id=job.id)

    # Segregation of Duties: Submitting Placement Officer cannot approve their own job
    if locked_job.submitted_by_id == user.id and not user.is_superuser:
        raise ValidationError("Segregation of Duties Violation: Submitting Placement Officer cannot approve their own job.")

    # Role validation
    user_roles = user.get_roles() if hasattr(user, "get_roles") else []
    if not (user.is_superuser or RoleCatalog.PLACEMENT_HEAD in user_roles or RoleCatalog.ADMIN in user_roles):
        raise ValidationError("Only authorized Placement Head or Administrator can approve job requirements.")

    # Status pre-condition
    if locked_job.status != JobStatusChoices.PENDING_APPROVAL:
        raise ValidationError(f"Job is in '{locked_job.status}' status. Only jobs in 'PENDING_APPROVAL' can be approved.")

    # Mandatory 5-point verification checklist check
    if not locked_job.is_all_checks_verified:
        raise ValidationError("Approval Denied: All 5 mandatory verification checks must reach VERIFIED before approval.")

    from_st = locked_job.status
    locked_job.status = JobStatusChoices.APPROVED
    locked_job.approved_by = user
    locked_job.approved_at = timezone.now()
    locked_job.updated_by = user
    locked_job.save(update_fields=["status", "approved_by", "approved_at", "updated_by", "updated_at"])

    JobWorkflowHistory.objects.create(
        job=locked_job,
        from_status=from_st,
        to_status=locked_job.status,
        actor=user,
        action="APPROVE_JOB",
        notes=notes.strip() or f"Formally approved by {user.email}.",
    )

    AuditLog.objects.create(
        user=user,
        action="JOB_APPROVED",
        resource_type="jobs.JobRequirement",
        resource_id=str(locked_job.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "approved_by": str(user.id),
            "approved_at": str(locked_job.approved_at),
            "revision_number": locked_job.revision_number,
        },
    )

    return locked_job


@transaction.atomic
def reject_job(
    *,
    job: JobRequirement,
    reason: str,
    user: User,
) -> JobRequirement:
    """Rejects a JobRequirement with mandatory justification."""
    locked_job = JobRequirement.objects.select_for_update().get(id=job.id)

    if not reason.strip():
        raise ValidationError({"reason": "A documented reason is required to reject a job requirement."})

    user_roles = user.get_roles() if hasattr(user, "get_roles") else []
    if not (user.is_superuser or RoleCatalog.PLACEMENT_HEAD in user_roles or RoleCatalog.ADMIN in user_roles):
        raise ValidationError("Only authorized Placement Head or Administrator can reject job requirements.")

    from_st = locked_job.status
    locked_job.status = JobStatusChoices.REJECTED
    locked_job.rejected_by = user
    locked_job.rejected_at = timezone.now()
    locked_job.rejection_reason = reason.strip()
    locked_job.updated_by = user
    locked_job.save(update_fields=["status", "rejected_by", "rejected_at", "rejection_reason", "updated_by", "updated_at"])

    JobWorkflowHistory.objects.create(
        job=locked_job,
        from_status=from_st,
        to_status=locked_job.status,
        actor=user,
        action="REJECT_JOB",
        notes=reason.strip(),
    )

    AuditLog.objects.create(
        user=user,
        action="JOB_REJECTED",
        resource_type="jobs.JobRequirement",
        resource_id=str(locked_job.id),
        correlation_id=get_current_correlation_id(),
        changes={"rejected_by": str(user.id), "reason": reason.strip()},
    )

    return locked_job


@transaction.atomic
def amend_approved_job(
    *,
    job: JobRequirement,
    reason: str,
    user: User,
    **fields,
) -> JobRequirement:
    """Authorized amendment of an APPROVED job, creating a new revision and requiring re-verification."""
    locked_job = JobRequirement.objects.select_for_update().get(id=job.id)

    if locked_job.status != JobStatusChoices.APPROVED:
        raise ValidationError(f"Cannot amend a job that is in '{locked_job.status}' status (must be APPROVED).")

    if not reason.strip():
        raise ValidationError({"reason": "An amendment reason is required to revise an approved job."})

    user_roles = user.get_roles() if hasattr(user, "get_roles") else []
    if not (user.is_superuser or RoleCatalog.PLACEMENT_HEAD in user_roles or RoleCatalog.ADMIN in user_roles):
        raise ValidationError("Only Placement Head or Administrator can authorize amendments to approved jobs.")

    old_revision = locked_job.revision_number
    locked_job.revision_number += 1
    from_st = locked_job.status

    # Apply updates
    changes: Dict[str, Any] = {}
    invalidated_checks: List[str] = []

    for check_type, material_fields in MATERIAL_FIELDS_MAPPING.items():
        for field_name in material_fields:
            if field_name in fields and getattr(locked_job, field_name) != fields[field_name]:
                invalidated_checks.append(check_type)
                break

    updatable_fields = [
        "title",
        "description",
        "role_category",
        "required_skills",
        "min_cgpa",
        "min_percentage",
        "eligible_batches",
        "eligible_branches",
        "max_backlogs_allowed",
        "min_ctc_lpa",
        "max_ctc_lpa",
        "stipend_amount",
        "salary_details",
        "job_location",
        "work_arrangement",
        "has_bond",
        "bond_duration_months",
        "bond_details",
        "interview_rounds",
        "interview_process_notes",
        "interview_date",
        "registration_deadline",
        "vacancies_count",
    ]

    for key in updatable_fields:
        if key in fields:
            val = fields[key]
            current_val = getattr(locked_job, key)
            if current_val != val:
                changes[key] = {"old": str(current_val), "new": str(val)}
                setattr(locked_job, key, val)

    # Invalidate all or affected checks and reset status to UNDER_VERIFICATION
    locked_job.status = JobStatusChoices.UNDER_VERIFICATION
    locked_job.approved_by = None
    locked_job.approved_at = None
    locked_job.updated_by = user
    locked_job.full_clean()
    locked_job.save()

    # If specific checks were identified, invalidate them; if none matched specifically, invalidate all
    checks_to_invalidate = invalidated_checks or list(VerificationCheckTypeChoices.values)
    for c_type in checks_to_invalidate:
        check = locked_job.verification_checks.filter(check_type=c_type).first()
        if check:
            check.status = CheckStatusChoices.PENDING
            check.requires_reverification = True
            check.invalidation_reason = f"Revision #{locked_job.revision_number}: {reason.strip()}"
            check.save()

    JobWorkflowHistory.objects.create(
        job=locked_job,
        from_status=from_st,
        to_status=locked_job.status,
        actor=user,
        action="AMEND_APPROVED_JOB",
        notes=f"Revision #{locked_job.revision_number} initiated by {user.email}. Reason: {reason.strip()}",
    )

    AuditLog.objects.create(
        user=user,
        action="JOB_APPROVED_AMENDMENT",
        resource_type="jobs.JobRequirement",
        resource_id=str(locked_job.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "old_revision": old_revision,
            "new_revision": locked_job.revision_number,
            "reason": reason.strip(),
            "field_changes": changes,
            "invalidated_checks": checks_to_invalidate,
        },
    )

    return locked_job

