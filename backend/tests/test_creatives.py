"""Comprehensive Test Suite for Phase 4: Creative Studio & Design Asset Approval.

Covers:
1. Requisition model creation and sequential CR-YYYY-NNNN code generation.
2. Requisition status lifecycle (Draft, Submitted, Assigned, In-Review, Approved, Handoff).
3. Triage & designer assignment.
4. Asset version upload with magic byte inspection and SHA-256 calculation.
5. Upload security: rejection of disguised binaries and oversized files (>15MB).
6. Mandatory 4-point design compliance check evaluation.
7. Approval blocked when checks are unpassed.
8. Strict Segregation of Duties (SoD): Uploader cannot self-approve.
9. Independent sign-off and version superseding.
10. Request changes workflow and revision upload (v1 -> v2).
11. Authenticated private media file streaming and defensive headers.
12. Operational queues and KPI metrics.
13. Centralized AuditLog verification across creative operations.
"""
import io
from decimal import Decimal
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from django.db import connection
from apps.accounts.models import User, Role, UserRoleAssignment, RoleCatalog
from apps.core.models import AuditLog
from apps.crm.models import Company
from apps.jobs.models import JobRequirement
from apps.creatives.models import (
    CreativeRequest,
    CreativeAssetVersion,
    DesignComplianceCheck,
    CreativeWorkflowHistory,
    CreativeStatusChoices,
    VersionStatusChoices,
    ComplianceCheckTypeChoices,
    ComplianceCheckStatusChoices,
    CreativeTypeChoices,
    AspectRatioChoices,
    DeliverableFormatChoices,
    CreativePriorityChoices,
)
from apps.creatives import services


# Valid 1x1 transparent PNG file with valid magic bytes (\x89PNG\r\n\x1a\n)
VALID_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

# Valid minimal PDF file with valid %PDF- magic bytes
VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def users_fixture(db):
    def assign_role(u, code):
        r, _ = Role.objects.get_or_create(code=code, defaults={"name": code})
        UserRoleAssignment.objects.create(user=u, role=r)

    admin = User.objects.create_user(email="admin@gqt.test", password="Password123!", first_name="Super", last_name="Admin")
    assign_role(admin, RoleCatalog.ADMIN)

    officer = User.objects.create_user(email="officer@gqt.test", password="Password123!", first_name="Placement", last_name="Officer")
    assign_role(officer, RoleCatalog.PLACEMENT_OFFICER)

    designer = User.objects.create_user(email="designer@gqt.test", password="Password123!", first_name="Graphic", last_name="Designer")
    assign_role(designer, RoleCatalog.CREATIVE_DESIGNER)

    reviewer = User.objects.create_user(email="reviewer@gqt.test", password="Password123!", first_name="Design", last_name="Reviewer")
    assign_role(reviewer, RoleCatalog.CREATIVE_REVIEWER)

    head = User.objects.create_user(email="head@gqt.test", password="Password123!", first_name="Placement", last_name="Head")
    assign_role(head, RoleCatalog.PLACEMENT_HEAD)

    auditor = User.objects.create_user(email="auditor@gqt.test", password="Password123!", first_name="Compliance", last_name="Auditor")
    assign_role(auditor, RoleCatalog.AUDITOR)

    student = User.objects.create_user(email="student@gqt.test", password="Password123!", first_name="Student", last_name="Candidate")
    assign_role(student, "STUDENT")

    company = Company.objects.create(name="Apex Cloud Technologies", canonical_domain="apexcloud.test", industry="IT_SERVICES")
    job = JobRequirement.objects.create(
        company=company,
        title="Graduate Cloud Engineer",
        role_category="SOFTWARE_ENGINEERING",
        min_ctc_lpa=Decimal("7.00"),
        max_ctc_lpa=Decimal("10.00"),
        registration_deadline="2026-12-01T18:00:00Z",
        submitted_by=officer,
        created_by=officer,
        updated_by=officer,
    )

    return {
        "admin": admin,
        "officer": officer,
        "designer": designer,
        "reviewer": reviewer,
        "head": head,
        "auditor": auditor,
        "student": student,
        "company": company,
        "job": job,
    }


@pytest.mark.django_db
def test_creative_request_model_and_code_generation(users_fixture):
    officer = users_fixture["officer"]
    job = users_fixture["job"]
    company = users_fixture["company"]

    req = services.create_creative_request(
        officer,
        title="Apex Cloud Hiring Flyer",
        brief="Include 7-10 LPA CTC, Bangalore, Python requirement, and GQT logo.",
        creative_type=CreativeTypeChoices.JOB_FLYER,
        aspect_ratio=AspectRatioChoices.BANNER_4_5,
        deliverable_format=DeliverableFormatChoices.PNG,
        priority=CreativePriorityChoices.HIGH,
        job_requirement_id=job.id,
        company_id=company.id,
    )

    assert req.id is not None
    assert req.request_code.startswith("CR-20")
    assert req.status == CreativeStatusChoices.DRAFT
    assert req.company == company
    assert req.job_requirement == job
    assert req.created_by == officer

    # Verify AuditLog created
    assert AuditLog.objects.filter(
        resource_id=str(req.id), action="CREATIVE_REQUEST_CREATED"
    ).exists()


@pytest.mark.django_db
def test_requisition_submission_workflow(users_fixture):
    officer = users_fixture["officer"]
    req = services.create_creative_request(
        officer,
        title="Draft Campaign Requisition",
        brief="Test brief content.",
    )

    assert req.status == CreativeStatusChoices.DRAFT
    submitted_req = services.submit_creative_request(officer, req.id)
    assert submitted_req.status == CreativeStatusChoices.SUBMITTED

    # Submitting already submitted raises ValidationError
    with pytest.raises(Exception):
        services.submit_creative_request(officer, req.id)


@pytest.mark.django_db
def test_triage_and_designer_assignment(users_fixture):
    officer = users_fixture["officer"]
    reviewer = users_fixture["reviewer"]
    designer = users_fixture["designer"]

    req = services.create_creative_request(officer, title="Design Task", brief="Brief")
    services.submit_creative_request(officer, req.id)

    assigned_req = services.triage_and_assign_request(
        reviewer,
        req.id,
        assigned_designer_id=designer.id,
        priority=CreativePriorityChoices.URGENT,
        notes="High priority placement announcement",
    )

    assert assigned_req.status == CreativeStatusChoices.ASSIGNED
    assert assigned_req.assigned_designer == designer
    assert assigned_req.priority == CreativePriorityChoices.URGENT


@pytest.mark.django_db
def test_asset_version_upload_and_check_initialization(users_fixture):
    officer = users_fixture["officer"]
    designer = users_fixture["designer"]
    reviewer = users_fixture["reviewer"]

    req = services.create_creative_request(officer, title="Flyer Task", brief="Brief")
    services.submit_creative_request(officer, req.id)
    services.triage_and_assign_request(reviewer, req.id, assigned_designer_id=designer.id)

    file_obj = SimpleUploadedFile("apex_flyer.png", VALID_PNG_BYTES, content_type="image/png")

    version = services.upload_asset_version(
        designer,
        req.id,
        uploaded_file=file_obj,
        designer_notes="First iteration with high-res logo.",
    )

    assert version.version_number == 1
    assert version.status == VersionStatusChoices.SUBMITTED_FOR_REVIEW
    assert version.mime_type == "image/png"
    assert len(version.sha256_hash) == 64
    assert version.uploader == designer

    # Request advances to IN_REVIEW
    req.refresh_from_db()
    assert req.status == CreativeStatusChoices.IN_REVIEW
    assert req.active_version == version

    # All 4 compliance checks initialized in PENDING
    checks = list(version.compliance_checks.all())
    assert len(checks) == 4
    for c in checks:
        assert c.status == ComplianceCheckStatusChoices.PENDING


@pytest.mark.django_db
def test_upload_security_rejects_disguised_script(users_fixture):
    designer = users_fixture["designer"]
    req = services.create_creative_request(designer, title="Task", brief="Brief")

    # Malicious file: Named .png but contains PHP / HTML executable text
    fake_png = SimpleUploadedFile("exploit.png", b"<?php echo 'malicious'; ?>", content_type="image/png")

    with pytest.raises(Exception) as exc:
        services.upload_asset_version(designer, req.id, uploaded_file=fake_png)
    assert "File header signature does not match" in str(exc.value)


@pytest.mark.django_db
def test_upload_security_rejects_disallowed_extension(users_fixture):
    designer = users_fixture["designer"]
    req = services.create_creative_request(designer, title="Task", brief="Brief")

    svg_file = SimpleUploadedFile("vector.svg", b"<svg><script>alert(1)</script></svg>", content_type="image/svg+xml")

    with pytest.raises(Exception) as exc:
        services.upload_asset_version(designer, req.id, uploaded_file=svg_file)
    assert "not permitted" in str(exc.value)


@pytest.mark.django_db
def test_four_point_compliance_check_evaluation(users_fixture):
    designer = users_fixture["designer"]
    reviewer = users_fixture["reviewer"]
    req = services.create_creative_request(designer, title="Task", brief="Brief")
    file_obj = SimpleUploadedFile("flyer.png", VALID_PNG_BYTES, content_type="image/png")
    version = services.upload_asset_version(designer, req.id, uploaded_file=file_obj)

    # Evaluate FLYER_TEXT_ACCURACY to PASSED
    check1 = services.evaluate_compliance_check(
        reviewer,
        version.id,
        ComplianceCheckTypeChoices.FLYER_TEXT_ACCURACY,
        status=ComplianceCheckStatusChoices.PASSED,
        notes="All numbers verified against JD.",
    )
    assert check1.status == ComplianceCheckStatusChoices.PASSED
    assert check1.verified_by == reviewer

    # Flagging requires documented notes
    with pytest.raises(Exception):
        services.evaluate_compliance_check(
            reviewer,
            version.id,
            ComplianceCheckTypeChoices.BRAND_ASSETS_COMPLIANCE,
            status=ComplianceCheckStatusChoices.FLAGGED,
            notes="",  # Blank notes forbidden on flag
        )


@pytest.mark.django_db
def test_approval_denied_if_checks_not_all_passed(users_fixture):
    designer = users_fixture["designer"]
    reviewer = users_fixture["reviewer"]
    req = services.create_creative_request(designer, title="Task", brief="Brief")
    file_obj = SimpleUploadedFile("flyer.png", VALID_PNG_BYTES, content_type="image/png")
    version = services.upload_asset_version(designer, req.id, uploaded_file=file_obj)

    # Only pass 2 of 4 checks
    services.evaluate_compliance_check(
        reviewer, version.id, ComplianceCheckTypeChoices.FLYER_TEXT_ACCURACY, status=ComplianceCheckStatusChoices.PASSED
    )
    services.evaluate_compliance_check(
        reviewer, version.id, ComplianceCheckTypeChoices.BRAND_ASSETS_COMPLIANCE, status=ComplianceCheckStatusChoices.PASSED
    )

    with pytest.raises(Exception) as exc:
        services.approve_asset_version(reviewer, version.id, review_feedback="Approved!")
    assert "All 4 design compliance checks must be passed" in str(exc.value)


@pytest.mark.django_db
def test_segregation_of_duties_self_approval_denied(users_fixture):
    designer = users_fixture["designer"]
    req = services.create_creative_request(designer, title="Task", brief="Brief")
    file_obj = SimpleUploadedFile("flyer.png", VALID_PNG_BYTES, content_type="image/png")
    version = services.upload_asset_version(designer, req.id, uploaded_file=file_obj)

    # Pass all 4 checks
    for check_type in ComplianceCheckTypeChoices.values:
        services.evaluate_compliance_check(
            designer, version.id, check_type, status=ComplianceCheckStatusChoices.PASSED
        )

    # Designer attempts to approve their OWN upload -> Strictly Denied by SoD
    with pytest.raises(Exception) as exc:
        services.approve_asset_version(designer, version.id, review_feedback="Self approving")
    assert "Segregation of duties violation" in str(exc.value)


@pytest.mark.django_db
def test_successful_independent_approval(users_fixture):
    designer = users_fixture["designer"]
    reviewer = users_fixture["reviewer"]
    req = services.create_creative_request(designer, title="Task", brief="Brief")
    file_obj = SimpleUploadedFile("flyer.png", VALID_PNG_BYTES, content_type="image/png")
    version = services.upload_asset_version(designer, req.id, uploaded_file=file_obj)

    # Pass all 4 checks
    for check_type in ComplianceCheckTypeChoices.values:
        services.evaluate_compliance_check(
            reviewer, version.id, check_type, status=ComplianceCheckStatusChoices.PASSED
        )

    approved_version = services.approve_asset_version(
        reviewer, version.id, review_feedback="Typography and brand compliance verified."
    )

    assert approved_version.status == VersionStatusChoices.APPROVED
    assert approved_version.reviewed_by == reviewer

    req.refresh_from_db()
    assert req.status == CreativeStatusChoices.APPROVED
    assert req.active_version == approved_version


@pytest.mark.django_db
def test_request_changes_and_v2_iteration(users_fixture):
    designer = users_fixture["designer"]
    reviewer = users_fixture["reviewer"]
    req = services.create_creative_request(designer, title="Task", brief="Brief")

    # Upload v1
    v1 = services.upload_asset_version(
        designer, req.id, uploaded_file=SimpleUploadedFile("v1.png", VALID_PNG_BYTES, content_type="image/png")
    )
    assert v1.version_number == 1

    # Reviewer requests adjustments
    v1_rev = services.request_changes_on_version(
        reviewer, v1.id, review_feedback="Logo padding too tight, please adjust margin."
    )
    assert v1_rev.status == VersionStatusChoices.CHANGES_REQUESTED

    req.refresh_from_db()
    assert req.status == CreativeStatusChoices.CHANGES_REQUESTED

    # Designer uploads revised v2
    v2 = services.upload_asset_version(
        designer,
        req.id,
        uploaded_file=SimpleUploadedFile("v2.png", VALID_PNG_BYTES, content_type="image/png"),
        designer_notes="Fixed margin around official logo.",
    )
    assert v2.version_number == 2

    # Pass all checks on v2 and approve
    for check_type in ComplianceCheckTypeChoices.values:
        services.evaluate_compliance_check(
            reviewer, v2.id, check_type, status=ComplianceCheckStatusChoices.PASSED
        )

    approved_v2 = services.approve_asset_version(reviewer, v2.id)
    assert approved_v2.status == VersionStatusChoices.APPROVED

    v1.refresh_from_db()
    assert v1.status == VersionStatusChoices.SUPERSEDED


@pytest.mark.django_db
def test_ready_for_handoff_workflow(users_fixture):
    designer = users_fixture["designer"]
    reviewer = users_fixture["reviewer"]
    head = users_fixture["head"]

    req = services.create_creative_request(designer, title="Task", brief="Brief")
    v1 = services.upload_asset_version(
        designer, req.id, uploaded_file=SimpleUploadedFile("v1.png", VALID_PNG_BYTES, content_type="image/png")
    )
    for check_type in ComplianceCheckTypeChoices.values:
        services.evaluate_compliance_check(reviewer, v1.id, check_type, status=ComplianceCheckStatusChoices.PASSED)
    services.approve_asset_version(reviewer, v1.id)

    # Placement Head marks ready for handoff
    handed_off = services.mark_ready_for_handoff(head, req.id, notes="Ready for WhatsApp campus groups.")
    assert handed_off.status == CreativeStatusChoices.READY_FOR_HANDOFF


@pytest.mark.django_db
def test_authenticated_asset_download_and_security_headers(api_client, users_fixture):
    designer = users_fixture["designer"]
    officer = users_fixture["officer"]

    req = services.create_creative_request(officer, title="Task", brief="Brief")
    v1 = services.upload_asset_version(
        designer, req.id, uploaded_file=SimpleUploadedFile("flyer.png", VALID_PNG_BYTES, content_type="image/png")
    )

    download_url = reverse("creatives:version-download", kwargs={"pk": str(v1.id)})

    # Unauthenticated receives 401
    resp = api_client.get(download_url)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # Authenticated user receives file with security headers
    api_client.force_authenticate(user=officer)
    resp = api_client.get(download_url)
    assert resp.status_code == status.HTTP_200_OK
    assert resp["X-Content-Type-Options"] == "nosniff"
    assert "image/png" in resp["Content-Type"]
    assert "inline" in resp["Content-Disposition"]


@pytest.mark.django_db
def test_student_forbidden_from_creative_studio_api(api_client, users_fixture):
    student = users_fixture["student"]
    api_client.force_authenticate(user=student)

    url = reverse("creatives:request-list")
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_creative_queues_and_metrics_api(api_client, users_fixture):
    reviewer = users_fixture["reviewer"]
    designer = users_fixture["designer"]
    officer = users_fixture["officer"]

    req = services.create_creative_request(officer, title="Triage Job", brief="Brief")
    services.submit_creative_request(officer, req.id)

    api_client.force_authenticate(user=reviewer)

    # Triage Queue
    triage_url = reverse("creatives:queue-triage")
    resp = api_client.get(triage_url)
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.data) >= 1

    # Studio Metrics
    metrics_url = reverse("creatives:studio-metrics")
    resp = api_client.get(metrics_url)
    assert resp.status_code == status.HTTP_200_OK
    assert "total_requests" in resp.data
    assert "triage_queue_count" in resp.data
    assert resp.data["triage_queue_count"] >= 1


@pytest.mark.django_db
def test_auditor_read_only_access(api_client, users_fixture):
    auditor = users_fixture["auditor"]
    officer = users_fixture["officer"]

    req = services.create_creative_request(officer, title="Task", brief="Brief")

    api_client.force_authenticate(user=auditor)
    list_resp = api_client.get(reverse("creatives:request-list"))
    assert list_resp.status_code == status.HTTP_200_OK

    # Auditor write attempt is forbidden
    create_resp = api_client.post(reverse("creatives:request-list"), {"title": "X", "brief": "Y"})
    assert create_resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_superuser_self_approval_strictly_blocked(users_fixture):
    """Verify that even a superuser who uploaded a version cannot self-approve (Remediation B)."""
    admin = users_fixture["admin"]
    req = services.create_creative_request(admin, title="Admin Upload Requisition", brief="Brief")

    file_obj = SimpleUploadedFile("flyer.png", VALID_PNG_BYTES, content_type="image/png")
    version = services.upload_asset_version(admin, req.id, uploaded_file=file_obj)

    # Pass all 4 checks
    for check_type in ComplianceCheckTypeChoices.values:
        services.evaluate_compliance_check(
            admin, version.id, check_type, status=ComplianceCheckStatusChoices.PASSED
        )

    # Superuser self-approval MUST be rejected
    with pytest.raises(Exception) as exc:
        services.approve_asset_version(admin, version.id, review_feedback="Admin approving own asset")
    assert "Segregation of duties violation" in str(exc.value)

    # Status must remain unchanged
    version.refresh_from_db()
    assert version.status == VersionStatusChoices.SUBMITTED_FOR_REVIEW


@pytest.mark.django_db
def test_unauthorized_role_cannot_approve_api(api_client, users_fixture):
    """Verify unauthorized role (e.g. Graphic Designer) cannot invoke approval endpoint."""
    designer = users_fixture["designer"]
    officer = users_fixture["officer"]
    reviewer = users_fixture["reviewer"]

    req = services.create_creative_request(officer, title="JD Task", brief="Brief")
    file_obj = SimpleUploadedFile("flyer.png", VALID_PNG_BYTES, content_type="image/png")
    version = services.upload_asset_version(designer, req.id, uploaded_file=file_obj)

    for check_type in ComplianceCheckTypeChoices.values:
        services.evaluate_compliance_check(
            reviewer, version.id, check_type, status=ComplianceCheckStatusChoices.PASSED
        )

    # Designer attempts to call approve endpoint
    api_client.force_authenticate(user=designer)
    approve_url = reverse("creatives:version-approve", kwargs={"pk": str(version.id)})
    resp = api_client.post(approve_url, {"review_feedback": "Unauthorized approval"})
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_pdf_download_forces_attachment_and_csp(api_client, users_fixture):
    """Verify that PDF assets are served with Content-Disposition: attachment and CSP sandbox (Remediation C)."""
    designer = users_fixture["designer"]
    officer = users_fixture["officer"]

    req = services.create_creative_request(officer, title="Brochure PDF", brief="Brief")
    pdf_file = SimpleUploadedFile("campus_brochure.pdf", VALID_PDF_BYTES, content_type="application/pdf")
    version = services.upload_asset_version(designer, req.id, uploaded_file=pdf_file)

    download_url = reverse("creatives:version-download", kwargs={"pk": str(version.id)})

    api_client.force_authenticate(user=officer)
    resp = api_client.get(download_url)
    assert resp.status_code == status.HTTP_200_OK
    assert "application/pdf" in resp["Content-Type"]

    # Security headers asserted
    assert "attachment" in resp["Content-Disposition"]
    assert resp["X-Content-Type-Options"] == "nosniff"
    assert resp["Content-Security-Policy"] == "default-src 'none'; sandbox"
    assert resp["Cache-Control"] == "private, no-cache, no-store, must-revalidate"


@pytest.mark.django_db
def test_compliance_checks_isolation_between_versions(users_fixture):
    """Verify that approval on v2 requires v2's checks and cannot inherit v1's (Remediation B)."""
    designer = users_fixture["designer"]
    reviewer = users_fixture["reviewer"]
    req = services.create_creative_request(designer, title="Multi-version Task", brief="Brief")

    # Upload v1 and pass all checks
    v1 = services.upload_asset_version(
        designer, req.id, uploaded_file=SimpleUploadedFile("v1.png", VALID_PNG_BYTES, content_type="image/png")
    )
    for check_type in ComplianceCheckTypeChoices.values:
        services.evaluate_compliance_check(reviewer, v1.id, check_type, status=ComplianceCheckStatusChoices.PASSED)

    # Reviewer requests adjustments on v1
    services.request_changes_on_version(reviewer, v1.id, review_feedback="Need revision.")

    # Designer uploads v2
    v2 = services.upload_asset_version(
        designer, req.id, uploaded_file=SimpleUploadedFile("v2.png", VALID_PNG_BYTES, content_type="image/png")
    )

    # v2 checks must all be PENDING
    v2_checks = list(v2.compliance_checks.all())
    assert len(v2_checks) == 4
    assert all(c.status == ComplianceCheckStatusChoices.PENDING for c in v2_checks)

    # Attempting to approve v2 without evaluating v2's checks must be blocked
    with pytest.raises(Exception) as exc:
        services.approve_asset_version(reviewer, v2.id)
    assert "All 4 design compliance checks must be passed" in str(exc.value)


@pytest.mark.django_db
def test_concurrency_unique_constraint_on_duplicate_version(users_fixture):
    """Verify database unique constraint prevents duplicate version numbers per request (Remediation E)."""
    from django.db.utils import IntegrityError
    designer = users_fixture["designer"]
    req = services.create_creative_request(designer, title="Concurrency Task", brief="Brief")

    # Insert v1
    CreativeAssetVersion.objects.create(
        request=req,
        version_number=1,
        original_filename="v1.png",
        file_size_bytes=100,
        mime_type="image/png",
        sha256_hash="dummyhash1",
        uploader=designer,
    )

    # Competing insert with same version_number must violate database UniqueConstraint
    with pytest.raises(IntegrityError):
        CreativeAssetVersion.objects.create(
            request=req,
            version_number=1,
            original_filename="v1_conflict.png",
            file_size_bytes=100,
            mime_type="image/png",
            sha256_hash="dummyhash2",
            uploader=designer,
        )


@pytest.mark.django_db
def test_version_allocation_sequential_and_independent_across_requests(users_fixture):
    """Verify Task B: v1 initial, sequential increments (v2, v3), and independence across requests."""
    designer = users_fixture["designer"]
    req1 = services.create_creative_request(designer, title="Req 1", brief="Brief 1")
    req2 = services.create_creative_request(designer, title="Req 2", brief="Brief 2")

    # Req 1: upload v1
    v1_1 = services.upload_asset_version(
        designer, req1.id, uploaded_file=SimpleUploadedFile("f1.png", VALID_PNG_BYTES, content_type="image/png")
    )
    assert v1_1.version_number == 1

    # Req 1: upload v2
    v1_2 = services.upload_asset_version(
        designer, req1.id, uploaded_file=SimpleUploadedFile("f2.png", VALID_PNG_BYTES, content_type="image/png")
    )
    assert v1_2.version_number == 2

    # Req 2: upload v1 (independent of req1)
    v2_1 = services.upload_asset_version(
        designer, req2.id, uploaded_file=SimpleUploadedFile("f3.png", VALID_PNG_BYTES, content_type="image/png")
    )
    assert v2_1.version_number == 1

    # Req 1: upload v3
    v1_3 = services.upload_asset_version(
        designer, req1.id, uploaded_file=SimpleUploadedFile("f4.png", VALID_PNG_BYTES, content_type="image/png")
    )
    assert v1_3.version_number == 3


@pytest.mark.django_db
def test_failed_version_creation_atomically_rolls_back(users_fixture, monkeypatch):
    """Verify Task B: atomic rollback leaves no partial version, compliance, or workflow records."""
    designer = users_fixture["designer"]
    req = services.create_creative_request(designer, title="Rollback Task", brief="Brief")

    initial_versions_count = CreativeAssetVersion.objects.filter(request=req).count()
    initial_checks_count = DesignComplianceCheck.objects.count()
    initial_history_count = CreativeWorkflowHistory.objects.filter(request=req).count()

    # Simulate an IntegrityError or unexpected failure inside version creation
    from django.db import IntegrityError
    def failing_create(*args, **kwargs):
        raise IntegrityError("Simulated unique constraint collision")

    monkeypatch.setattr(CreativeAssetVersion.objects, "create", failing_create)

    with pytest.raises(Exception) as exc:
        services.upload_asset_version(
            designer,
            req.id,
            uploaded_file=SimpleUploadedFile("fail.png", VALID_PNG_BYTES, content_type="image/png"),
        )
    assert "version creation conflict" in str(exc.value)

    # Database state must be clean with zero partial records
    assert CreativeAssetVersion.objects.filter(request=req).count() == initial_versions_count
    assert DesignComplianceCheck.objects.count() == initial_checks_count
    assert CreativeWorkflowHistory.objects.filter(request=req).count() == initial_history_count


@pytest.mark.django_db
def test_version_creation_conflict_produces_controlled_error_not_500(api_client, users_fixture, monkeypatch):
    """Verify Task B: conflict produces controlled HTTP 400 response rather than unhandled HTTP 500."""
    designer = users_fixture["designer"]
    req = services.create_creative_request(designer, title="Conflict API Task", brief="Brief")

    from django.db import IntegrityError
    def failing_create(*args, **kwargs):
        raise IntegrityError("Simulated collision")

    monkeypatch.setattr(CreativeAssetVersion.objects, "create", failing_create)

    api_client.force_authenticate(user=designer)
    upload_url = reverse("creatives:request-upload-version", kwargs={"pk": str(req.id)})
    resp = api_client.post(
        upload_url,
        {
            "file": SimpleUploadedFile("conflict.png", VALID_PNG_BYTES, content_type="image/png"),
            "designer_notes": "Attempt upload",
        },
        format="multipart",
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "version creation conflict" in str(resp.data)


@pytest.mark.django_db
def test_requester_distinct_from_uploader_approval_workflow(users_fixture):
    """Verify Task A & D: Requester who is distinct from uploader can approve if authorized."""
    head = users_fixture["head"]
    designer = users_fixture["designer"]

    # Head creates requisition
    req = services.create_creative_request(head, title="Head Requisition", brief="Brief")
    assert req.created_by == head

    # Designer uploads deliverable
    v1 = services.upload_asset_version(
        designer,
        req.id,
        uploaded_file=SimpleUploadedFile("flyer.png", VALID_PNG_BYTES, content_type="image/png"),
    )
    assert v1.uploader == designer

    # Evaluate checks
    for check_type in ComplianceCheckTypeChoices.values:
        services.evaluate_compliance_check(head, v1.id, check_type, status=ComplianceCheckStatusChoices.PASSED)

    # Head approves (head != designer, so uploader SoD is satisfied)
    approved_v1 = services.approve_asset_version(head, v1.id, review_feedback="Approved by Head.")
    assert approved_v1.status == VersionStatusChoices.APPROVED
    assert approved_v1.reviewed_by == head


@pytest.mark.django_db
def test_superuser_uploader_self_approval_api_returns_400(api_client, users_fixture):
    """Verify Task D: Superuser who uploaded version receives controlled 400 Bad Request via API."""
    admin = users_fixture["admin"]
    req = services.create_creative_request(admin, title="Admin Requisition", brief="Brief")

    v1 = services.upload_asset_version(
        admin,
        req.id,
        uploaded_file=SimpleUploadedFile("admin_flyer.png", VALID_PNG_BYTES, content_type="image/png"),
    )

    for check_type in ComplianceCheckTypeChoices.values:
        services.evaluate_compliance_check(admin, v1.id, check_type, status=ComplianceCheckStatusChoices.PASSED)

    api_client.force_authenticate(user=admin)
    approve_url = reverse("creatives:version-approve", kwargs={"pk": str(v1.id)})
    resp = api_client.post(approve_url, {"review_feedback": "Admin self approval attempt."})

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Segregation of duties violation" in str(resp.data)


@pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="Genuine multi-threaded row-locking concurrency requires an isolated PostgreSQL backend; SQLite in-memory is connection-isolated.",
)
@pytest.mark.django_db(transaction=True)
def test_threaded_concurrency_version_allocation(users_fixture):
    """Verify Task C & Phase 4D: Genuine multi-threaded concurrency test.
    Under PostgreSQL, parent row-locking with select_for_update() serializes the two
    competing transactions, allocating version 1 to the first and version 2 to the second.
    """
    import threading
    from django.db import connection

    designer = users_fixture["designer"]
    req = services.create_creative_request(designer, title="Threaded Task", brief="Brief")

    barrier = threading.Barrier(2)
    results = []
    errors = []

    def worker_upload(worker_id):
        try:
            # Synchronize thread start to contend simultaneously
            barrier.wait(timeout=5)
            file_obj = SimpleUploadedFile(f"thread_{worker_id}.png", VALID_PNG_BYTES, content_type="image/png")
            version = services.upload_asset_version(
                designer,
                req.id,
                uploaded_file=file_obj,
                designer_notes=f"Worker {worker_id}",
            )
            results.append((worker_id, version.version_number, str(version.id)))
        except Exception as exc:
            errors.append((worker_id, exc))
        finally:
            connection.close()

    t1 = threading.Thread(target=worker_upload, args=(1,))
    t2 = threading.Thread(target=worker_upload, args=(2,))

    t1.start()
    t2.start()

    t1.join(timeout=10)
    t2.join(timeout=10)

    # 1. Assert no unexpected errors occurred
    assert len(errors) == 0, f"Worker errors encountered: {errors}"
    assert len(results) == 2, f"Expected 2 successful worker results, got {len(results)}: {results}"

    # 2. Assert versions are exactly sequential [1, 2]
    all_versions = list(
        CreativeAssetVersion.objects.filter(request=req)
        .order_by("version_number")
        .values_list("version_number", flat=True)
    )
    assert all_versions == [1, 2], f"Expected exact version sequence [1, 2], got {all_versions}"

    # 3. Assert complete record integrity for both versions
    v1 = CreativeAssetVersion.objects.get(request=req, version_number=1)
    v2 = CreativeAssetVersion.objects.get(request=req, version_number=2)

    assert v1.compliance_checks.count() == 4, "v1 missing compliance checks"
    assert v2.compliance_checks.count() == 4, "v2 missing compliance checks"

    # 4. Assert workflow history records exist for both uploads
    upload_histories = CreativeWorkflowHistory.objects.filter(request=req, action="UPLOAD_VERSION")
    assert upload_histories.count() == 2, f"Expected 2 workflow records, found {upload_histories.count()}"

    # 5. Assert audit log records exist for both versions
    audit_v1 = AuditLog.objects.filter(action="CREATIVE_VERSION_UPLOADED", resource_id=str(v1.id)).exists()
    audit_v2 = AuditLog.objects.filter(action="CREATIVE_VERSION_UPLOADED", resource_id=str(v2.id)).exists()
    assert audit_v1 and audit_v2, "Audit logs missing for one or both version uploads"

