"""Domain Services and Step 23 Placement Readiness Certification Gate (MOD-006)."""
from typing import Optional, List
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.jobs.models import JobRequirement
from apps.students.models import StudentProfile, StudentResume
from apps.preparation.models import (
    ResumeReview,
    AssessmentRecord,
    MockInterview,
    ReadinessCertification,
    ResumeReviewStatusChoices,
)


def evaluate_readiness_criteria(
    student: StudentProfile,
    job: JobRequirement,
) -> Tuple_Readiness:
    """Evaluate whether candidate meets all three prerequisites for Step 23 certification."""
    missing: List[str] = []

    # 1. Approved / Verified Resume
    has_approved_review = ResumeReview.objects.filter(
        student=student, status=ResumeReviewStatusChoices.APPROVED
    ).exists()
    has_verified_resume = StudentResume.objects.filter(
        student=student, is_verified=True
    ).exists()

    if not (has_approved_review or has_verified_resume):
        missing.append("Verified and approved placement resume is required.")

    # 2. Passed Technical Assessment
    has_passed_tech = AssessmentRecord.objects.filter(
        student=student, is_passed=True
    ).exists()

    if not has_passed_tech:
        missing.append("Cleared technical assessment record is required.")

    # 3. Recommended Mock Interview
    has_rec_mock = MockInterview.objects.filter(
        student=student, is_recommended=True
    ).exists()

    if not has_rec_mock:
        missing.append("Conducted and recommended mock interview scorecard is required.")

    can_certify = len(missing) == 0
    return can_certify, missing


Tuple_Readiness = tuple[bool, list[str]]


def certify_student_readiness(
    student: StudentProfile,
    job: JobRequirement,
    certified_by: User,
    notes: str = "",
) -> ReadinessCertification:
    """Step 23 Hard Gate: Enforce verification before granting Readiness Certification."""
    can_certify, missing = evaluate_readiness_criteria(student, job)

    if not can_certify:
        error_msg = "; ".join(missing)
        raise ValidationError(f"Cannot grant readiness certification: {error_msg}")

    cert, _ = ReadinessCertification.objects.update_or_create(
        student=student,
        job=job,
        defaults={
            "is_certified": True,
            "certified_by": certified_by,
            "certified_at": timezone.now(),
            "certification_notes": notes.strip(),
        },
    )

    AuditLog.objects.create(
        user=certified_by,
        action="READINESS_CERTIFIED",
        resource_type="ReadinessCertification",
        resource_id=str(cert.id),
        changes={
            "student": student.roll_number,
            "job": job.title,
            "certified_by": certified_by.email,
        },
    )

    return cert
