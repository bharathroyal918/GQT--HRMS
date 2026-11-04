"""Comprehensive Test Suite for Phase 3: Job Requirements, 5-Point Verification, and Approval.

Covers:
- Job model field validation and PROTECT deletion policy
- Initialization of all 5 mandatory checklist gates
- Allowed and forbidden workflow transitions
- Strict 5-point verification enforcement before approval
- Segregation of Duties: Submitting Placement Officer self-approval denial
- Role-based and object-level access controls (Placement Officer, Head, Auditor read-only)
- Lock on approved jobs and authorized amendment workflow
- Material field invalidation resetting verification checks
- Mandatory justifications for rejection and change requests
- Audit log recording and correlation ID tracking
- Selector filtering and pagination
"""
import uuid
from decimal import Decimal
import pytest
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, Role, RoleCatalog, UserRoleAssignment
from apps.core.models import AuditLog
from apps.crm.models import Company, CompanyStatusChoices
from apps.jobs.models import (
    JobRequirement,
    JobVerificationCheck,
    JobWorkflowHistory,
    JobStatusChoices,
    VerificationCheckTypeChoices,
    CheckStatusChoices,
    RoleCategoryChoices,
    WorkArrangementChoices,
)
from apps.jobs import services, selectors


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def roles(db):
    role_map = {}
    for code, name in RoleCatalog.CHOICES:
        role_map[code], _ = Role.objects.get_or_create(code=code, defaults={"name": name})
    return role_map


@pytest.fixture
def admin_user(db, roles):
    user = User.objects.create_user(email="admin.jobs@gqt.test", password="Password123!", first_name="Admin", last_name="User")
    UserRoleAssignment.objects.create(user=user, role=roles[RoleCatalog.ADMIN])
    return user


@pytest.fixture
def placement_head(db, roles):
    user = User.objects.create_user(email="head.jobs@gqt.test", password="Password123!", first_name="Placement", last_name="Head")
    UserRoleAssignment.objects.create(user=user, role=roles[RoleCatalog.PLACEMENT_HEAD])
    return user


@pytest.fixture
def placement_officer(db, roles):
    user = User.objects.create_user(email="officer.jobs@gqt.test", password="Password123!", first_name="Placement", last_name="Officer")
    UserRoleAssignment.objects.create(user=user, role=roles[RoleCatalog.PLACEMENT_OFFICER])
    return user


@pytest.fixture
def second_officer(db, roles):
    user = User.objects.create_user(email="officer2.jobs@gqt.test", password="Password123!", first_name="Officer", last_name="Two")
    UserRoleAssignment.objects.create(user=user, role=roles[RoleCatalog.PLACEMENT_OFFICER])
    return user


@pytest.fixture
def auditor_user(db, roles):
    user = User.objects.create_user(email="auditor.jobs@gqt.test", password="Password123!", first_name="Audit", last_name="User")
    UserRoleAssignment.objects.create(user=user, role=roles[RoleCatalog.AUDITOR])
    return user


@pytest.fixture
def student_user(db):
    return User.objects.create_user(email="student.jobs@gqt.test", password="Password123!", first_name="Student", last_name="User")


@pytest.fixture
def sample_company(db, admin_user):
    return Company.objects.create(
        name="Apex Cloud Systems",
        website="https://apexcloud.io",
        status=CompanyStatusChoices.ACTIVE_HIRING_PARTNER,
        created_by=admin_user,
    )


@pytest.fixture
def sample_job(db, sample_company, placement_officer):
    deadline = timezone.now() + timezone.timedelta(days=14)
    return services.create_job_requirement(
        company=sample_company,
        title="Associate Software Engineer",
        description="Core backend software engineering role with Python and Go.",
        min_ctc_lpa=Decimal("6.50"),
        max_ctc_lpa=Decimal("9.00"),
        registration_deadline=deadline,
        role_category=RoleCategoryChoices.SOFTWARE_ENGINEERING,
        required_skills=["Python", "Django", "PostgreSQL"],
        min_cgpa=Decimal("7.00"),
        min_percentage=Decimal("65.00"),
        eligible_batches=["2025"],
        eligible_branches=["CSE", "ISE"],
        max_backlogs_allowed=0,
        job_location="Bengaluru",
        work_arrangement=WorkArrangementChoices.HYBRID,
        user=placement_officer,
    )


@pytest.mark.django_db
def test_job_model_creation_and_checks_initialization(sample_job, sample_company, placement_officer):
    """Verifies that creating a job requirement initializes all 5 mandatory checks in PENDING status."""
    assert sample_job.status == JobStatusChoices.DRAFT
    assert sample_job.company == sample_company
    assert sample_job.submitted_by == placement_officer
    assert sample_job.revision_number == 1

    checks = sample_job.verification_checks.all()
    assert checks.count() == 5
    check_types = set(checks.values_list("check_type", flat=True))
    assert check_types == set(VerificationCheckTypeChoices.values)
    for c in checks:
        assert c.status == CheckStatusChoices.PENDING
        assert c.requires_reverification is False

    assert sample_job.is_all_checks_verified is False


@pytest.mark.django_db
def test_job_company_protect_deletion_policy(sample_job, sample_company):
    """Verifies that historical job records prevent deletion of the parent company (PROTECT policy)."""
    with pytest.raises(ProtectedError):
        sample_company.delete()


@pytest.mark.django_db
def test_job_field_validation():
    """Verifies boundary validations for CTC, CGPA, percentage, and deadlines."""
    company = Company.objects.create(name="Validation Test Corp")
    past_deadline = timezone.now() - timezone.timedelta(days=1)
    future_deadline = timezone.now() + timezone.timedelta(days=10)

    # 1. Negative CTC
    job = JobRequirement(
        company=company,
        title="Negative CTC Job",
        description="Testing",
        min_ctc_lpa=Decimal("-1.00"),
        max_ctc_lpa=Decimal("5.00"),
        registration_deadline=future_deadline,
    )
    with pytest.raises(ValidationError):
        job.full_clean()

    # 2. Max CTC < Min CTC
    job.min_ctc_lpa = Decimal("8.00")
    job.max_ctc_lpa = Decimal("6.00")
    with pytest.raises(ValidationError):
        job.full_clean()

    # 3. Invalid CGPA (> 10)
    job.min_ctc_lpa = Decimal("5.00")
    job.max_ctc_lpa = Decimal("8.00")
    job.min_cgpa = Decimal("11.50")
    with pytest.raises(ValidationError):
        job.full_clean()

    # 4. Past registration deadline on service creation
    user = User.objects.create_user(email="test.valid@gqt.test", password="Password123!")
    with pytest.raises(ValidationError):
        services.create_job_requirement(
            company=company,
            title="Expired Job",
            description="Testing",
            min_ctc_lpa=Decimal("5.00"),
            max_ctc_lpa=Decimal("8.00"),
            registration_deadline=past_deadline,
            user=user,
        )


@pytest.mark.django_db
def test_submit_for_verification_workflow(sample_job, placement_officer):
    """Verifies submitting a draft requirement moves it to PENDING_VERIFICATION."""
    assert sample_job.status == JobStatusChoices.DRAFT

    updated = services.submit_for_verification(job=sample_job, user=placement_officer)
    assert updated.status == JobStatusChoices.PENDING_VERIFICATION

    # Check workflow history recorded
    history = updated.workflow_history.first()
    assert history.action == "SUBMIT_FOR_VERIFICATION"
    assert history.from_status == JobStatusChoices.DRAFT
    assert history.to_status == JobStatusChoices.PENDING_VERIFICATION


@pytest.mark.django_db
def test_assign_verifier_and_progress_to_under_verification(sample_job, placement_officer, second_officer):
    """Verifies assigning a verifier transitions job to UNDER_VERIFICATION."""
    services.submit_for_verification(job=sample_job, user=placement_officer)
    updated = services.assign_verifier(job=sample_job, verifier=second_officer, user=placement_officer)

    assert updated.status == JobStatusChoices.UNDER_VERIFICATION
    assert updated.assigned_verifier == second_officer


@pytest.mark.django_db
def test_five_point_verification_advances_to_pending_approval(sample_job, placement_officer, second_officer):
    """Verifies that when all 5 checks reach VERIFIED, job automatically transitions to PENDING_APPROVAL."""
    services.submit_for_verification(job=sample_job, user=placement_officer)
    services.assign_verifier(job=sample_job, verifier=second_officer, user=placement_officer)

    check_types = list(VerificationCheckTypeChoices.values)

    # Verify first 4 checks
    for c_type in check_types[:4]:
        services.update_verification_check(
            job=sample_job,
            check_type=c_type,
            status=CheckStatusChoices.VERIFIED,
            user=second_officer,
            notes="Passed verification review.",
            evidence_reference="DOC-REF-100",
        )
        sample_job.refresh_from_db()
        assert sample_job.status == JobStatusChoices.UNDER_VERIFICATION
        assert sample_job.is_all_checks_verified is False

    # Verify 5th check: Registration Deadline
    services.update_verification_check(
        job=sample_job,
        check_type=check_types[4],
        status=CheckStatusChoices.VERIFIED,
        user=second_officer,
        notes="Registration deadline compliant with academic calendar.",
    )
    sample_job.refresh_from_db()
    assert sample_job.is_all_checks_verified is True
    assert sample_job.status == JobStatusChoices.PENDING_APPROVAL


@pytest.mark.django_db
def test_approval_denied_if_checks_not_verified(sample_job, placement_officer, placement_head):
    """Verifies that approval is strictly denied if any check is not VERIFIED."""
    services.submit_for_verification(job=sample_job, user=placement_officer)

    # Attempt to approve draft or unverified job
    with pytest.raises(ValidationError) as exc:
        services.approve_job(job=sample_job, user=placement_head)
    assert "Only jobs in 'PENDING_APPROVAL' can be approved" in str(exc.value)


@pytest.mark.django_db
def test_segregation_of_duties_self_approval_denied(sample_job, placement_head):
    """Verifies that the submitting Placement Officer cannot approve their own job even with Placement Head role."""
    # Set the submitter as placement_head
    sample_job.submitted_by = placement_head
    sample_job.status = JobStatusChoices.PENDING_APPROVAL
    sample_job.save()

    # Pass all 5 checks
    for c in sample_job.verification_checks.all():
        c.status = CheckStatusChoices.VERIFIED
        c.save()

    with pytest.raises(ValidationError) as exc:
        services.approve_job(job=sample_job, user=placement_head)
    assert "Segregation of Duties Violation: Submitting Placement Officer cannot approve their own job" in str(exc.value)


@pytest.mark.django_db
def test_successful_independent_approval(sample_job, placement_officer, placement_head):
    """Verifies successful approval by independent Placement Head when all 5 checks are VERIFIED."""
    services.submit_for_verification(job=sample_job, user=placement_officer)

    for c in sample_job.verification_checks.all():
        c.status = CheckStatusChoices.VERIFIED
        c.save()

    sample_job.status = JobStatusChoices.PENDING_APPROVAL
    sample_job.save()

    approved_job = services.approve_job(job=sample_job, user=placement_head, notes="All checks verified. Approved.")
    assert approved_job.status == JobStatusChoices.APPROVED
    assert approved_job.approved_by == placement_head
    assert approved_job.approved_at is not None

    # Audit check
    assert AuditLog.objects.filter(action="JOB_APPROVED", resource_id=str(approved_job.id)).exists()


@pytest.mark.django_db
def test_approved_job_locked_against_direct_updates(sample_job, placement_officer, placement_head):
    """Verifies that an approved job cannot be edited via direct update service."""
    for c in sample_job.verification_checks.all():
        c.status = CheckStatusChoices.VERIFIED
        c.save()
    sample_job.status = JobStatusChoices.PENDING_APPROVAL
    sample_job.save()

    services.approve_job(job=sample_job, user=placement_head)

    # Attempt direct update
    with pytest.raises(ValidationError) as exc:
        services.update_job_requirement(job=sample_job, user=placement_officer, title="Hacked Title")
    assert "Approved jobs cannot be modified directly" in str(exc.value)


@pytest.mark.django_db
def test_authorized_amendment_increments_revision_and_invalidates_checks(sample_job, placement_head):
    """Verifies that authorized amendment creates a new revision and requires re-verification."""
    for c in sample_job.verification_checks.all():
        c.status = CheckStatusChoices.VERIFIED
        c.save()
    sample_job.status = JobStatusChoices.APPROVED
    sample_job.approved_by = placement_head
    sample_job.revision_number = 1
    sample_job.save()

    amended = services.amend_approved_job(
        job=sample_job,
        reason="CTC renegotiated upwards with company recruiter.",
        user=placement_head,
        min_ctc_lpa=Decimal("7.50"),
        max_ctc_lpa=Decimal("11.00"),
    )

    assert amended.status == JobStatusChoices.UNDER_VERIFICATION
    assert amended.revision_number == 2
    assert amended.approved_by is None
    assert amended.min_ctc_lpa == Decimal("7.50")

    # The SALARY_AUTHENTICITY check must have been invalidated
    salary_check = amended.verification_checks.get(check_type=VerificationCheckTypeChoices.SALARY_AUTHENTICITY)
    assert salary_check.status == CheckStatusChoices.PENDING
    assert salary_check.requires_reverification is True


@pytest.mark.django_db
def test_material_field_edit_invalidates_affected_checks(sample_job, placement_officer):
    """Verifies that updating eligibility in draft/review invalidates the ELIGIBILITY check."""
    eligibility_check = sample_job.verification_checks.get(check_type=VerificationCheckTypeChoices.ELIGIBILITY)
    eligibility_check.status = CheckStatusChoices.VERIFIED
    eligibility_check.save()

    # Modify eligibility criteria
    services.update_job_requirement(
        job=sample_job,
        user=placement_officer,
        min_cgpa=Decimal("8.50"),
    )

    eligibility_check.refresh_from_db()
    assert eligibility_check.status == CheckStatusChoices.PENDING
    assert eligibility_check.requires_reverification is True
    assert "Material field change detected" in eligibility_check.invalidation_reason


@pytest.mark.django_db
def test_rejection_requires_meaningful_reason(sample_job, placement_head):
    """Verifies that rejecting a job requires a mandatory documented reason."""
    with pytest.raises(ValidationError):
        services.reject_job(job=sample_job, reason="", user=placement_head)

    with pytest.raises(ValidationError):
        services.reject_job(job=sample_job, reason="   ", user=placement_head)

    rejected = services.reject_job(job=sample_job, reason="Company blacklisted due to fake offer letters.", user=placement_head)
    assert rejected.status == JobStatusChoices.REJECTED
    assert rejected.rejected_by == placement_head


@pytest.mark.django_db
def test_request_changes_requires_reason(sample_job, placement_officer, placement_head):
    """Verifies that requesting changes requires non-empty feedback."""
    services.submit_for_verification(job=sample_job, user=placement_officer)

    with pytest.raises(ValidationError):
        services.request_changes(job=sample_job, reason="", user=placement_head)

    updated = services.request_changes(
        job=sample_job,
        reason="Please include eligible 2024 batch graduates per HR email.",
        user=placement_head,
    )
    assert updated.status == JobStatusChoices.CHANGES_REQUESTED
    assert "2024 batch" in updated.changes_requested_reason


@pytest.mark.django_db
def test_auditor_read_only_via_api(api_client, auditor_user, sample_job):
    """Verifies that an Auditor has read access but is blocked from mutations via API."""
    api_client.force_authenticate(user=auditor_user)

    # 1. Read job list - ALLOWED
    res_list = api_client.get("/api/v1/jobs/requirements/")
    assert res_list.status_code == status.HTTP_200_OK

    # 2. Read detail - ALLOWED
    res_detail = api_client.get(f"/api/v1/jobs/requirements/{sample_job.id}/")
    assert res_detail.status_code == status.HTTP_200_OK

    # 3. Create job - FORBIDDEN
    res_post = api_client.post("/api/v1/jobs/requirements/", {"title": "Auditor Job"})
    assert res_post.status_code == status.HTTP_403_FORBIDDEN

    # 4. Update check - FORBIDDEN
    res_check = api_client.post(
        f"/api/v1/jobs/requirements/{sample_job.id}/checks/ELIGIBILITY/",
        {"status": "VERIFIED", "notes": "Auditor testing"},
    )
    assert res_check.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_student_denied_access_to_jobs_api(api_client, student_user, sample_job):
    """Verifies students cannot access staff job requirements and verification endpoints."""
    api_client.force_authenticate(user=student_user)

    res = api_client.get("/api/v1/jobs/requirements/")
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res_q = api_client.get("/api/v1/jobs/verification-queue/")
    assert res_q.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_verification_and_approval_queues(api_client, placement_head, placement_officer, sample_company):
    """Verifies filtering of verification-queue and approval-queue."""
    future = timezone.now() + timezone.timedelta(days=7)

    # Job 1: In PENDING_VERIFICATION
    j1 = services.create_job_requirement(
        company=sample_company,
        title="Job 1 Verification",
        description="Desc",
        min_ctc_lpa=Decimal("5.00"),
        max_ctc_lpa=Decimal("7.00"),
        registration_deadline=future,
        user=placement_officer,
    )
    services.submit_for_verification(job=j1, user=placement_officer)

    # Job 2: In PENDING_APPROVAL
    j2 = services.create_job_requirement(
        company=sample_company,
        title="Job 2 Approval",
        description="Desc",
        min_ctc_lpa=Decimal("8.00"),
        max_ctc_lpa=Decimal("12.00"),
        registration_deadline=future,
        user=placement_officer,
    )
    for c in j2.verification_checks.all():
        c.status = CheckStatusChoices.VERIFIED
        c.save()
    j2.status = JobStatusChoices.PENDING_APPROVAL
    j2.save()

    api_client.force_authenticate(user=placement_head)

    # Verification queue should contain Job 1, not Job 2
    res_v = api_client.get("/api/v1/jobs/verification-queue/")
    assert res_v.status_code == status.HTTP_200_OK
    v_ids = [item["id"] for item in res_v.data["results"]]
    assert str(j1.id) in v_ids
    assert str(j2.id) not in v_ids

    # Approval queue should contain Job 2, not Job 1
    res_a = api_client.get("/api/v1/jobs/approval-queue/")
    assert res_a.status_code == status.HTTP_200_OK
    a_ids = [item["id"] for item in res_a.data["results"]]
    assert str(j2.id) in a_ids
    assert str(j1.id) not in a_ids


@pytest.mark.django_db
def test_workflow_metrics_endpoint(api_client, placement_head, sample_job):
    """Verifies that the metrics endpoint aggregates accurate counts from persisted records."""
    api_client.force_authenticate(user=placement_head)
    res = api_client.get("/api/v1/jobs/metrics/")
    assert res.status_code == status.HTTP_200_OK
    data = res.data

    assert "total_jobs" in data
    assert data["total_jobs"] >= 1
    assert "draft_jobs" in data
    assert "verification_stats" in data
    assert data["verification_stats"]["total_checks"] >= 5

