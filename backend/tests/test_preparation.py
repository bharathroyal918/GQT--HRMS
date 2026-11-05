"""Integration tests for Student Preparation & Step 23 Readiness Certification Gate (MOD-006)."""
from decimal import Decimal
import pytest
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import RoleCatalog
from apps.accounts.services import create_user, assign_role
from apps.crm.services import create_company
from apps.jobs.services import create_job_requirement
from apps.students.models import StudentProfile, StudentResume
from apps.preparation.models import (
    ResumeReview,
    AssessmentRecord,
    MockInterview,
    ReadinessCertification,
    ResumeReviewStatusChoices,
    MockStatusChoices,
)
from apps.preparation.services import (
    evaluate_readiness_criteria,
    certify_student_readiness,
)


@pytest.fixture
def admin_user(db):
    user = create_user(email="admin_prep@gqt.local", password="Password@123", is_staff=True)
    assign_role(user, RoleCatalog.ADMIN)
    return user


@pytest.fixture
def trainer_user(db):
    user = create_user(email="trainer_prep@gqt.local", password="Password@123")
    assign_role(user, RoleCatalog.TRAINER)
    return user


@pytest.fixture
def candidate(db):
    return StudentProfile.objects.create(
        roll_number="GQT-PREP-001",
        full_name="Pooja Patel",
        email="pooja@gqt.local",
        phone="+919876543299",
        degree="B.Tech",
        branch="CSE",
        graduation_year=2025,
        cgpa=Decimal("8.80"),
        backlogs_count=0,
    )


@pytest.fixture
def sample_job(db, admin_user):
    company = create_company(name="Prep Global Technologies", user=admin_user)
    job = create_job_requirement(
        company=company,
        title="Full Stack Software Engineer",
        description="Full stack opportunity across modern web stacks.",
        role_category="SOFTWARE_ENGINEERING",
        work_arrangement="ONSITE",
        min_cgpa=Decimal("7.50"),
        eligible_batches=["2025"],
        eligible_branches=["CSE", "IT"],
        max_backlogs_allowed=0,
        min_ctc_lpa=Decimal("7.00"),
        max_ctc_lpa=Decimal("9.00"),
        registration_deadline=timezone.now() + timezone.timedelta(days=10),
        user=admin_user,
    )
    return job


@pytest.mark.django_db
def test_step23_hard_gate_blocks_uncertified_candidate_with_missing_prerequisites(candidate, sample_job, admin_user):
    """Step 23 Gate: Candidate cannot be certified if resume unverified, test not passed, and mock not done."""
    can_certify, missing = evaluate_readiness_criteria(candidate, sample_job)
    assert can_certify is False
    assert len(missing) == 3

    with pytest.raises(ValidationError) as exc:
        certify_student_readiness(candidate, sample_job, certified_by=admin_user)
    assert "Cannot grant readiness certification" in str(exc.value)


@pytest.mark.django_db
def test_step23_hard_gate_succeeds_when_all_prerequisites_are_satisfied(candidate, sample_job, admin_user, trainer_user):
    """Step 23 Gate: Satisfying verified resume + passed technical test + recommended mock enables certification."""
    # 1. Approved resume review
    ResumeReview.objects.create(
        student=candidate,
        job=sample_job,
        reviewer=trainer_user,
        score=Decimal("9.0"),
        status=ResumeReviewStatusChoices.APPROVED,
        notes="Clean formatting, strong project metrics.",
    )

    # 2. Passed technical assessment
    AssessmentRecord.objects.create(
        student=candidate,
        job=sample_job,
        test_type="TECHNICAL",
        score=Decimal("82.00"),
        max_score=Decimal("100.00"),
        pass_threshold=Decimal("60.00"),
        conducted_at=timezone.now(),
    )

    # 3. Recommended mock interview
    MockInterview.objects.create(
        student=candidate,
        job=sample_job,
        interviewer=trainer_user,
        scheduled_date=timezone.now(),
        conducted_date=timezone.now(),
        status=MockStatusChoices.CONDUCTED,
        technical_score=Decimal("22.0"),
        communication_score=Decimal("14.0"),
        problem_solving_score=Decimal("9.0"),
        is_recommended=True,
    )

    # Re-evaluate
    can_certify, missing = evaluate_readiness_criteria(candidate, sample_job)
    assert can_certify is True
    assert len(missing) == 0

    # Execute Certification
    cert = certify_student_readiness(
        student=candidate,
        job=sample_job,
        certified_by=admin_user,
        notes="Ready for Infosys/TCS corporate drive.",
    )
    assert cert.is_certified is True
    assert cert.certified_by == admin_user


@pytest.mark.django_db
def test_evaluate_readiness_criteria_annotation_and_return_structure(candidate, sample_job):
    """Regression test: evaluate_readiness_criteria return structure & Tuple_Readiness type resolution."""
    import importlib
    import typing
    import apps.preparation.services as prep_services

    # Verify module re-imports cleanly without NameError or startup failure
    importlib.reload(prep_services)

    # Verify type annotations resolve cleanly without error
    type_hints = typing.get_type_hints(prep_services.evaluate_readiness_criteria)
    assert "return" in type_hints
    assert type_hints["return"] == tuple[bool, list[str]]

    # Verify return value is a 2-tuple conforming to (bool, list[str])
    res = prep_services.evaluate_readiness_criteria(candidate, sample_job)
    assert isinstance(res, tuple)
    assert len(res) == 2
    can_certify, missing = res
    assert isinstance(can_certify, bool)
    assert isinstance(missing, list)
    assert all(isinstance(item, str) for item in missing)
