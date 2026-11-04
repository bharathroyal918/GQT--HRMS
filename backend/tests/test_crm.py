"""Recruitment CRM Phase 2 Tests: Company, HR Contacts, Outreach, and Follow-Ups."""
import uuid
import pytest
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.services import create_user, assign_role
from apps.accounts.models import RoleCatalog
from apps.core.models import AuditLog
from apps.crm.models import (
    Company,
    HRContact,
    OutreachActivity,
    FollowUp,
    CompanyStatusChoices,
    FollowUpStatusChoices,
    OutreachOutcomeChoices,
    OutreachChannelChoices,
    IndustryChoices,
    normalize_company_name,
    extract_canonical_domain,
)
from apps.crm.services import (
    create_company,
    update_company,
    detect_company_duplicates,
    create_hr_contact,
    update_hr_contact,
    log_outreach_activity,
    create_follow_up,
    complete_follow_up,
    cancel_follow_up,
)


@pytest.fixture
def admin_user(db):
    user = create_user(email="crm.admin@gqt.local", password="AdminPass123!", is_staff=True)
    assign_role(user, RoleCatalog.ADMIN)
    return user


@pytest.fixture
def calling_exec(db):
    user = create_user(email="calling.exec@gqt.local", password="CallerPass123!")
    assign_role(user, RoleCatalog.CALLING_EXECUTIVE)
    return user


@pytest.fixture
def crm_exec(db):
    user = create_user(email="crm.exec@gqt.local", password="CrmPass123!")
    assign_role(user, RoleCatalog.CRM_EXECUTIVE)
    return user


@pytest.fixture
def auditor_user(db):
    user = create_user(email="auditor@gqt.local", password="AuditorPass123!")
    assign_role(user, RoleCatalog.AUDITOR)
    return user


@pytest.fixture
def trainer_user(db):
    user = create_user(email="trainer@gqt.local", password="TrainerPass123!")
    assign_role(user, RoleCatalog.TRAINER)
    return user


# --- 1. Model Normalization & Domain Extraction ---

def test_company_normalization_and_domain_extraction():
    """Verify name cleaning and domain canonicalization functions."""
    assert normalize_company_name("Infosys Technologies Pvt. Ltd.") == "infosys technologies"
    assert normalize_company_name("Wipro Enterprise Limited") == "wipro enterprise"
    assert extract_canonical_domain("https://www.google.com/careers") == "google.com"
    assert extract_canonical_domain("http://tcs.in:8080/path") == "tcs.in"


@pytest.mark.django_db
def test_company_model_save_normalization():
    """Verify Company.save() populates normalized_name and canonical_domain."""
    comp = Company.objects.create(
        name="Cognizant Technology Solutions India Pvt. Ltd.",
        website="https://www.cognizant.com",
    )
    assert isinstance(comp.id, uuid.UUID)
    assert comp.normalized_name == "cognizant technology solutions india"
    assert comp.canonical_domain == "cognizant.com"


# --- 2. Deduplication Engine ---

@pytest.mark.django_db
def test_duplicate_detection_exact_domain():
    """Verify duplicate detection flags matching domain."""
    create_company(
        name="Tata Consultancy Services",
        website="https://www.tcs.com",
    )
    dup = detect_company_duplicates(name="TCS Digital", website="http://tcs.com/jobs")
    assert dup["is_duplicate"] is True
    assert dup["matches"][0]["match_reason"] == "EXACT_DOMAIN_MATCH"


@pytest.mark.django_db
def test_duplicate_creation_rejected_unless_allowed():
    """Verify create_company raises ValidationError on domain conflict without allow_duplicate flag."""
    create_company(
        name="Amazon India",
        website="https://www.amazon.in",
    )
    with pytest.raises(ValidationError, match="already exists"):
        create_company(
            name="Amazon Web Services",
            website="https://amazon.in",
            allow_duplicate=False,
        )

    # Allowed duplicate with explicit flag
    allowed = create_company(
        name="Amazon Operations",
        website="https://amazon.in",
        allow_duplicate=True,
    )
    assert allowed.id is not None


# --- 3. HR Contact Management & Primary Toggle ---

@pytest.mark.django_db
def test_hr_contact_creation_and_primary_toggle(admin_user):
    """Verify multiple contacts and automatic demotion of previous primary contact."""
    comp = create_company(name="Zoho Corporation", website="https://zoho.com", user=admin_user)

    c1 = create_hr_contact(
        company=comp,
        name="Alice Recruiter",
        email="alice@zoho.com",
        phone="+91 98765 43210",
        is_primary=True,
        user=admin_user,
    )
    assert c1.is_primary is True
    assert c1.phone == "+919876543210"

    # Add second contact marked as primary
    c2 = create_hr_contact(
        company=comp,
        name="Bob HR Head",
        email="bob@zoho.com",
        is_primary=True,
        user=admin_user,
    )
    c1.refresh_from_db()
    assert c1.is_primary is False
    assert c2.is_primary is True


# --- 4. Outreach Logging & Lifecycle Progression ---

@pytest.mark.django_db
def test_outreach_logging_advances_company_status(calling_exec):
    """Verify positive outreach advances company status from LEAD to ENGAGED."""
    comp = create_company(name="Freshworks", status=CompanyStatusChoices.LEAD, user=calling_exec)
    assert comp.status == CompanyStatusChoices.LEAD

    activity = log_outreach_activity(
        company=comp,
        executive=calling_exec,
        channel=OutreachChannelChoices.PHONE,
        outcome=OutreachOutcomeChoices.INTERESTED,
        notes="HR expressed interest in campus hiring for 2027 batch.",
        follow_up_date=timezone.now() + timezone.timedelta(days=2),
    )
    comp.refresh_from_db()
    assert comp.status == CompanyStatusChoices.ENGAGED

    # Verify auto-scheduled follow-up
    assert FollowUp.objects.filter(company=comp, outreach_activity=activity).exists()


# --- 5. Follow-Up Task Lifecycle ---

@pytest.mark.django_db
def test_follow_up_lifecycle(calling_exec):
    """Verify scheduling, completing, and overdue calculation."""
    comp = create_company(name="Accenture", user=calling_exec)
    past_due = timezone.now() - timezone.timedelta(hours=2)

    task = create_follow_up(
        company=comp,
        assigned_to=calling_exec,
        title="Send Placement Brochure",
        due_date=past_due,
        user=calling_exec,
    )
    assert task.is_overdue is True
    assert task.status == FollowUpStatusChoices.PENDING

    # Complete task
    completed = complete_follow_up(follow_up=task, user=calling_exec, notes="Sent brochure via email.")
    assert completed.status == FollowUpStatusChoices.COMPLETED
    assert completed.is_overdue is False
    assert completed.completed_at is not None


# --- 6. Role-Based Permissions & API Access ---

@pytest.mark.django_db
def test_unauthenticated_requests_denied():
    """Verify anonymous access is rejected with 401."""
    client = APIClient()
    res = client.get("/api/v1/crm/companies/")
    assert res.status_code == 401


@pytest.mark.django_db
def test_auditor_read_only_enforcement(auditor_user):
    """Verify Auditor role can read companies but cannot create or modify them."""
    client = APIClient()
    client.force_authenticate(user=auditor_user)

    # Read allowed
    get_res = client.get("/api/v1/crm/companies/")
    assert get_res.status_code == 200

    # Write denied (403)
    post_res = client.post("/api/v1/crm/companies/", {"name": "Unauthorized Inc"}, format="json")
    assert post_res.status_code == 403


@pytest.mark.django_db
def test_unauthorized_role_denied(trainer_user):
    """Verify Trainer role has no access to CRM module."""
    client = APIClient()
    client.force_authenticate(user=trainer_user)
    res = client.get("/api/v1/crm/companies/")
    assert res.status_code == 403


@pytest.mark.django_db
def test_calling_executive_crud_flow(calling_exec):
    """Verify Calling Executive can create, view, and log outreach for companies."""
    client = APIClient()
    client.force_authenticate(user=calling_exec)

    create_res = client.post(
        "/api/v1/crm/companies/",
        {
            "name": "Target Tech Solutions",
            "website": "https://targettech.local",
            "industry": IndustryChoices.PRODUCT_TECH,
            "status": CompanyStatusChoices.LEAD,
        },
        format="json",
    )
    assert create_res.status_code == 201
    company_id = create_res.json()["id"]

    # Log outreach touchpoint
    outreach_res = client.post(
        f"/api/v1/crm/companies/{company_id}/outreach/",
        {
            "channel": OutreachChannelChoices.PHONE,
            "outcome": OutreachOutcomeChoices.FOLLOW_UP_REQUESTED,
            "notes": "Discussed hiring numbers. Requested callback on Monday.",
            "next_action": "Call TA Lead",
        },
        format="json",
    )
    assert outreach_res.status_code == 201
    assert outreach_res.json()["outcome"] == OutreachOutcomeChoices.FOLLOW_UP_REQUESTED


# --- 7. Audit Log Trail ---

@pytest.mark.django_db
def test_audit_logs_created_for_crm_actions(admin_user):
    """Verify immutable audit records for Company, Contact, and Follow-Up actions."""
    comp = create_company(name="Audit Test Corp", user=admin_user)
    contact = create_hr_contact(company=comp, name="Audit Recruiter", user=admin_user)
    follow_up = create_follow_up(
        company=comp,
        assigned_to=admin_user,
        title="Audit Follow-up",
        due_date=timezone.now() + timezone.timedelta(days=1),
        user=admin_user,
    )
    complete_follow_up(follow_up=follow_up, user=admin_user)

    assert AuditLog.objects.filter(action="COMPANY_CREATED", resource_id=str(comp.id)).exists()
    assert AuditLog.objects.filter(action="HR_CONTACT_CREATED", resource_id=str(contact.id)).exists()
    assert AuditLog.objects.filter(action="FOLLOWUP_COMPLETED", resource_id=str(follow_up.id)).exists()

