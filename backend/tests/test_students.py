"""Integration tests for Student Management & Eligibility Engine (MOD-005)."""
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
from apps.students.models import StudentProfile, DriveRegistration, EligibilityEvaluation
from apps.students.services import (
    evaluate_student_eligibility,
    register_student_for_job,
    override_student_eligibility,
    finalize_candidate_cohort,
)


@pytest.fixture
def admin_user(db):
    user = create_user(email="admin_students@gqt.local", password="Password@123", is_staff=True)
    assign_role(user, RoleCatalog.ADMIN)
    return user


@pytest.fixture
def officer_user(db):
    user = create_user(email="officer_students@gqt.local", password="Password@123")
    assign_role(user, RoleCatalog.PLACEMENT_OFFICER)
    return user


@pytest.fixture
def sample_job(db, officer_user):
    company = create_company(name="Test Software Corp", user=officer_user)
    job = create_job_requirement(
        company=company,
        title="Software Engineer - Backend",
        description="Comprehensive backend development opportunity.",
        role_category="SOFTWARE_ENGINEERING",
        work_arrangement="HYBRID",
        min_cgpa=Decimal("7.00"),
        eligible_batches=["2025", "2026"],
        eligible_branches=["CSE", "IT", "ECE"],
        max_backlogs_allowed=0,
        min_ctc_lpa=Decimal("6.50"),
        max_ctc_lpa=Decimal("8.50"),
        registration_deadline=timezone.now() + timezone.timedelta(days=7),
        user=officer_user,
    )
    return job


@pytest.fixture
def eligible_student(db):
    return StudentProfile.objects.create(
        roll_number="GQT-2025-001",
        full_name="Aarav Sharma",
        email="aarav@gqt.local",
        phone="+919876543210",
        degree="B.Tech",
        branch="CSE",
        graduation_year=2025,
        cgpa=Decimal("8.45"),
        backlogs_count=0,
    )


@pytest.fixture
def low_cgpa_student(db):
    return StudentProfile.objects.create(
        roll_number="GQT-2025-002",
        full_name="Rohan Verma",
        email="rohan@gqt.local",
        phone="+919876543211",
        degree="B.Tech",
        branch="CSE",
        graduation_year=2025,
        cgpa=Decimal("6.20"),  # Below 7.00
        backlogs_count=0,
    )


@pytest.fixture
def wrong_branch_student(db):
    return StudentProfile.objects.create(
        roll_number="GQT-2025-003",
        full_name="Kavita Nair",
        email="kavita@gqt.local",
        phone="+919876543212",
        degree="B.Tech",
        branch="ME",  # Mechanical - not in [CSE, IT, ECE]
        graduation_year=2025,
        cgpa=Decimal("8.10"),
        backlogs_count=0,
    )


@pytest.mark.django_db
def test_deterministic_eligibility_evaluation_passes_for_qualified_student(eligible_student, sample_job):
    is_eligible, failed_reasons, eval_record = evaluate_student_eligibility(eligible_student, sample_job)
    assert is_eligible is True
    assert len(failed_reasons) == 0
    assert eval_record.is_eligible is True


@pytest.mark.django_db
def test_deterministic_eligibility_fails_on_low_cgpa(low_cgpa_student, sample_job):
    is_eligible, failed_reasons, eval_record = evaluate_student_eligibility(low_cgpa_student, sample_job)
    assert is_eligible is False
    assert len(failed_reasons) == 1
    assert "CGPA 6.20 is below minimum requirement of 7.00" in failed_reasons[0]
    assert eval_record.is_eligible is False


@pytest.mark.django_db
def test_deterministic_eligibility_fails_on_ineligible_branch(wrong_branch_student, sample_job):
    is_eligible, failed_reasons, eval_record = evaluate_student_eligibility(wrong_branch_student, sample_job)
    assert is_eligible is False
    assert any("Academic branch 'ME' is not in eligible branches" in r for r in failed_reasons)


@pytest.mark.django_db
def test_registration_blocked_for_ineligible_candidate(low_cgpa_student, sample_job, officer_user):
    with pytest.raises(ValidationError) as exc:
        register_student_for_job(low_cgpa_student, sample_job, user=officer_user)
    assert "Student does not satisfy eligibility criteria" in str(exc.value)


@pytest.mark.django_db
def test_registration_succeeds_for_eligible_candidate(eligible_student, sample_job, officer_user):
    reg = register_student_for_job(eligible_student, sample_job, user=officer_user)
    assert reg.status == "REGISTERED"
    assert reg.student == eligible_student
    assert reg.job == sample_job


@pytest.mark.django_db
def test_manual_override_allows_borderline_registration(low_cgpa_student, sample_job, admin_user):
    is_eligible, failed_reasons, eval_record = evaluate_student_eligibility(low_cgpa_student, sample_job)
    assert is_eligible is False

    # Placement Head authorizes waiver
    override_student_eligibility(
        evaluation=eval_record,
        overridden_by=admin_user,
        reason="Approved academic council waiver for published research paper.",
    )
    eval_record.refresh_from_db()
    assert eval_record.manually_overridden is True
    assert eval_record.overridden_by == admin_user

    # Candidate can now register
    reg = register_student_for_job(low_cgpa_student, sample_job, user=admin_user)
    assert reg.status == "REGISTERED"


@pytest.mark.django_db
def test_cohort_finalization(eligible_student, sample_job, officer_user, admin_user):
    register_student_for_job(eligible_student, sample_job, user=officer_user)
    cohort = finalize_candidate_cohort(sample_job, user=admin_user)
    assert cohort.status == "FINALIZED"
    assert eligible_student in cohort.students.all()


@pytest.mark.django_db
def test_students_api_list_and_metrics(officer_user, eligible_student):
    client = APIClient()
    client.force_authenticate(user=officer_user)

    res = client.get("/api/v1/students/")
    assert res.status_code == status.HTTP_200_OK
    assert res.data["count"] >= 1

    res_metrics = client.get("/api/v1/students/metrics/")
    assert res_metrics.status_code == status.HTTP_200_OK
    assert res_metrics.data["total_students"] >= 1
