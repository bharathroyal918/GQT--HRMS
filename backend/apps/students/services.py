"""Domain Services and Deterministic Eligibility Engine (MOD-005)."""
from typing import Tuple, List, Optional
from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.accounts.models import RoleCatalog, User
from apps.core.models import AuditLog
from apps.jobs.models import JobRequirement
from apps.students.models import (
    StudentProfile,
    StudentResume,
    DriveRegistration,
    EligibilityEvaluation,
    CandidateCohort,
    CohortStatusChoices,
    RegistrationStatusChoices,
)


def evaluate_student_eligibility(
    student: StudentProfile,
    job: JobRequirement,
) -> Tuple[bool, List[str], EligibilityEvaluation]:
    """Execute deterministic eligibility verification across academic criteria."""
    failed_reasons: List[str] = []

    # 1. CGPA Threshold Check
    if job.min_cgpa is not None:
        if student.cgpa < job.min_cgpa:
            failed_reasons.append(
                f"CGPA {student.cgpa:.2f} is below minimum requirement of {job.min_cgpa:.2f}"
            )

    # 2. Percentage Check
    if job.min_percentage is not None:
        student_pct = student.twelfth_percentage or student.tenth_percentage or Decimal("0.00")
        if student_pct < job.min_percentage:
            failed_reasons.append(
                f"Aggregate percentage {student_pct:.2f}% is below minimum requirement of {job.min_percentage:.2f}%"
            )

    # 3. Maximum Backlogs Permitted Check
    if student.backlogs_count > job.max_backlogs_allowed:
        failed_reasons.append(
            f"Active backlogs count ({student.backlogs_count}) exceeds maximum permissible ({job.max_backlogs_allowed})"
        )

    # 4. Eligible Graduation Batch Check
    if job.eligible_batches:
        batches_str = [str(b).strip() for b in job.eligible_batches]
        if str(student.graduation_year) not in batches_str:
            failed_reasons.append(
                f"Graduation batch '{student.graduation_year}' is not in allowed batches ({', '.join(batches_str)})"
            )

    # 5. Eligible Branches / Disciplines Check
    if job.eligible_branches:
        branches_upper = [str(b).strip().upper() for b in job.eligible_branches]
        if student.branch.strip().upper() not in branches_upper:
            failed_reasons.append(
                f"Academic branch '{student.branch}' is not in eligible branches ({', '.join(branches_upper)})"
            )

    is_eligible = len(failed_reasons) == 0

    evaluation, _ = EligibilityEvaluation.objects.update_or_create(
        student=student,
        job=job,
        defaults={
            "is_eligible": is_eligible,
            "failed_criteria": failed_reasons,
            "evaluated_at": timezone.now(),
        },
    )

    return is_eligible, failed_reasons, evaluation


def register_student_for_job(
    student: StudentProfile,
    job: JobRequirement,
    user: Optional[User] = None,
) -> DriveRegistration:
    """Register student for a placement drive with deadline and eligibility enforcement."""
    # Check deadline
    if job.registration_deadline and timezone.now() > job.registration_deadline:
        raise ValidationError("Registration window for this placement drive is closed.")

    # Evaluate eligibility
    is_eligible, failed_reasons, evaluation = evaluate_student_eligibility(student, job)

    if not is_eligible and not evaluation.manually_overridden:
        reasons_msg = "; ".join(failed_reasons)
        raise ValidationError(f"Student does not satisfy eligibility criteria: {reasons_msg}")

    registration, created = DriveRegistration.objects.get_or_create(
        student=student,
        job=job,
        defaults={"status": RegistrationStatusChoices.REGISTERED},
    )

    if not created and registration.status == RegistrationStatusChoices.WITHDRAWN:
        registration.status = RegistrationStatusChoices.REGISTERED
        registration.save()

    if user:
        AuditLog.objects.create(
            user=user,
            action="DRIVE_REGISTRATION_CREATED",
            resource_type="DriveRegistration",
            resource_id=str(registration.id),
            changes={"student": student.roll_number, "job": job.title},
        )

    return registration


def override_student_eligibility(
    evaluation: EligibilityEvaluation,
    overridden_by: User,
    reason: str,
) -> EligibilityEvaluation:
    """Authorize manual override for borderline or special candidate waiver."""
    if not reason or len(reason.strip()) < 10:
        raise ValidationError("A clear justification (minimum 10 characters) is required for an eligibility override.")

    evaluation.manually_overridden = True
    evaluation.overridden_by = overridden_by
    evaluation.override_reason = reason.strip()
    evaluation.save()

    AuditLog.objects.create(
        user=overridden_by,
        action="ELIGIBILITY_MANUALLY_OVERRIDDEN",
        resource_type="EligibilityEvaluation",
        resource_id=str(evaluation.id),
        changes={
            "student": evaluation.student.roll_number,
            "job": evaluation.job.title,
            "reason": reason.strip(),
        },
    )

    return evaluation


@transaction.atomic
def finalize_candidate_cohort(
    job: JobRequirement,
    user: User,
) -> CandidateCohort:
    """Finalize candidate cohort including all eligible and overridden registered candidates."""
    cohort, _ = CandidateCohort.objects.get_or_create(job=job)

    # Fetch eligible registered students
    eligible_evals = EligibilityEvaluation.objects.filter(
        job=job
    ).filter(
        models.Q(is_eligible=True) | models.Q(manually_overridden=True)
    ).values_list("student_id", flat=True)

    registered_students = DriveRegistration.objects.filter(
        job=job,
        student_id__in=eligible_evals,
        status=RegistrationStatusChoices.REGISTERED,
    ).values_list("student_id", flat=True)

    cohort.students.set(registered_students)
    cohort.status = CohortStatusChoices.FINALIZED
    cohort.finalized_by = user
    cohort.finalized_at = timezone.now()
    cohort.save()

    AuditLog.objects.create(
        user=user,
        action="CANDIDATE_COHORT_FINALIZED",
        resource_type="CandidateCohort",
        resource_id=str(cohort.id),
        changes={
            "job_title": job.title,
            "students_count": len(registered_students),
        },
    )

    return cohort
