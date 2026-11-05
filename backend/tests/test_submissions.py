"""Integration tests for Candidate Submissions & Dispatch (MOD-007)."""
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
from apps.preparation.models import ReadinessCertification
from apps.submissions.models import SubmissionPackage, SubmissionItem, SubmissionStatusChoices
from apps.submissions.services import (
    create_submission_package,
    add_candidate_to_package,
    approve_submission_package,
    dispatch_submission_package,
    acknowledge_submission_package,
)


@pytest.fixture
def admin_user(db):
    user = create_user(email="admin_sub@gqt.local", password="Password@123", is_staff=True)
    assign_role(user, RoleCatalog.ADMIN)
    return user


@pytest.fixture
def head_user(db):
    user = create_user(email="head_sub@gqt.local", password="Password@123")
    assign_role(user, RoleCatalog.PLACEMENT_HEAD)
    return user


@pytest.fixture
def officer_user(db):
    user = create_user(email="officer_sub@gqt.local", password="Password@123")
    assign_role(user, RoleCatalog.PLACEMENT_OFFICER)
    return user


@pytest.fixture
def sample_job(db, officer_user):
    company = create_company(name="Amazon Web Services", user=officer_user)
    job = create_job_requirement(
        company=company,
        title="Cloud DevOps Associate",
        description="Global cloud infrastructure engineering role.",
        role_category="CLOUD_DEVOPS",
        work_arrangement="HYBRID",
        min_cgpa=Decimal("7.00"),
        eligible_batches=["2025"],
        eligible_branches=["CSE", "IT", "ECE"],
        max_backlogs_allowed=0,
        min_ctc_lpa=Decimal("8.00"),
        max_ctc_lpa=Decimal("12.00"),
        registration_deadline=timezone.now() + timezone.timedelta(days=7),
        user=officer_user,
    )
    return job


@pytest.fixture
def certified_student(db, sample_job, head_user):
    student = StudentProfile.objects.create(
        roll_number="GQT-CERT-001",
        full_name="Tanvi Rao",
        email="tanvi@gqt.local",
        phone="+919876543001",
        degree="B.Tech",
        branch="CSE",
        graduation_year=2025,
        cgpa=Decimal("9.10"),
        backlogs_count=0,
    )
    StudentResume.objects.create(
        student=student,
        version=1,
        file_name="tanvi_resume_v1.pdf",
        file_hash="hash-tanvi-1",
        is_verified=True,
    )
    ReadinessCertification.objects.create(
        student=student,
        job=sample_job,
        is_certified=True,
        certified_by=head_user,
    )
    return student


@pytest.fixture
def uncertified_student(db):
    return StudentProfile.objects.create(
        roll_number="GQT-UNCERT-002",
        full_name="Vikram Seth",
        email="vikram@gqt.local",
        phone="+919876543002",
        degree="B.Tech",
        branch="CSE",
        graduation_year=2025,
        cgpa=Decimal("7.80"),
        backlogs_count=0,
    )


@pytest.mark.django_db
def test_submission_package_lifecycle_and_step23_gate(sample_job, officer_user, head_user, certified_student, uncertified_student):
    # 1. Create package
    package = create_submission_package(
        job=sample_job,
        title="AWS Cloud Associates 2025 Roster",
        user=officer_user,
    )
    assert package.status == SubmissionStatusChoices.DRAFT
    assert package.package_code.startswith("SUB-")

    # 2. Try adding uncertified candidate -> MUST FAIL Step 23 Gate
    with pytest.raises(ValidationError) as exc:
        add_candidate_to_package(package=package, student=uncertified_student, user=officer_user)
    assert "cannot be added without active Step 23" in str(exc.value)

    # 3. Add certified candidate -> Succeeds
    item = add_candidate_to_package(package=package, student=certified_student, user=officer_user)
    assert item.student == certified_student
    assert item.resume_version == 1

    # 4. Placement Head approves package -> Calculates SHA-256 roster hash
    approved_pkg = approve_submission_package(package=package, user=head_user)
    assert approved_pkg.status == SubmissionStatusChoices.APPROVED
    assert len(approved_pkg.roster_hash) == 64

    # 5. Dispatch package to recruiter
    dispatch_log = dispatch_submission_package(
        package=approved_pkg,
        recipient_email="campus-recruiter@amazon.com",
        recipient_name="Campus Talent Team",
        user=officer_user,
    )
    assert dispatch_log.recipient_email == "campus-recruiter@amazon.com"
    approved_pkg.refresh_from_db()
    assert approved_pkg.status == SubmissionStatusChoices.DISPATCHED
    assert approved_pkg.dispatched_at is not None

    # 6. Recruiter acknowledges
    ack_pkg = acknowledge_submission_package(
        package=approved_pkg,
        user=officer_user,
        notes="HR confirmed interview shortlisting timeline.",
    )
    assert ack_pkg.status == SubmissionStatusChoices.ACKNOWLEDGED
    assert ack_pkg.acknowledged_at is not None


@pytest.mark.django_db
def test_submission_roster_csv_export(sample_job, officer_user, head_user, certified_student):
    package = create_submission_package(job=sample_job, title="AWS Roster", user=officer_user)
    add_candidate_to_package(package=package, student=certified_student, user=officer_user)

    client = APIClient()
    client.force_authenticate(user=officer_user)
    res = client.get(f"/api/v1/submissions/{package.id}/roster-csv/")
    assert res.status_code == status.HTTP_200_OK
    assert res["Content-Type"].startswith("text/csv")
    content = res.content.decode("utf-8")
    assert "Tanvi Rao" in content
    assert "GQT-CERT-001" in content

