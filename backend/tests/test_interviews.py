"""Integration tests for Placement Drives & Multi-Round Interviews (MOD-008)."""
from decimal import Decimal
import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import RoleCatalog
from apps.accounts.services import create_user, assign_role
from apps.crm.services import create_company
from apps.jobs.services import create_job_requirement
from apps.students.models import StudentProfile
from apps.interviews.models import PlacementDrive, InterviewRound, InterviewSlot


@pytest.fixture
def coordinator_user(db):
    user = create_user(email="coord_interview@gqt.local", password="Password@123")
    assign_role(user, RoleCatalog.INTERVIEW_COORDINATOR)
    return user


@pytest.fixture
def sample_job(db, coordinator_user):
    company = create_company(name="Google Cloud Partner", user=coordinator_user)
    job = create_job_requirement(
        company=company,
        title="Associate Software Engineer",
        description="Software development role across microservices.",
        role_category="SOFTWARE_ENGINEERING",
        work_arrangement="ONSITE",
        min_cgpa=Decimal("7.00"),
        eligible_batches=["2025"],
        eligible_branches=["CSE", "IT"],
        max_backlogs_allowed=0,
        min_ctc_lpa=Decimal("9.00"),
        max_ctc_lpa=Decimal("12.00"),
        registration_deadline=timezone.now() + timezone.timedelta(days=7),
        user=coordinator_user,
    )
    return job


@pytest.fixture
def candidate(db):
    return StudentProfile.objects.create(
        roll_number="GQT-INT-001",
        full_name="Meera Sen",
        email="meera@gqt.local",
        phone="+919876543011",
        degree="B.Tech",
        branch="CSE",
        graduation_year=2025,
        cgpa=Decimal("8.70"),
        backlogs_count=0,
    )


@pytest.mark.django_db
def test_placement_drive_and_interview_rounds_api(sample_job, candidate, coordinator_user):
    client = APIClient()
    client.force_authenticate(user=coordinator_user)

    # 1. Schedule a Placement Drive
    drive_payload = {
        "job_id": str(sample_job.id),
        "title": "Google Cloud On-Campus Drive 2025",
        "drive_date": (timezone.now() + timezone.timedelta(days=10)).isoformat(),
        "venue_or_link": "Auditorium Hall B & Google Meet",
        "drive_mode": "HYBRID",
    }
    res_drive = client.post("/api/v1/interviews/", drive_payload, format="json")
    assert res_drive.status_code == status.HTTP_201_CREATED
    drive_id = res_drive.data["id"]
    assert res_drive.data["drive_code"].startswith("DRV-")

    # 2. Add Round 1: Coding Challenge
    round_payload = {
        "round_number": 1,
        "round_type": "CODING",
        "round_name": "Online Coding Challenge",
        "instructions": "90 minutes on HackerRank platform.",
    }
    res_round = client.post(f"/api/v1/interviews/{drive_id}/rounds/", round_payload, format="json")
    assert res_round.status_code == status.HTTP_201_CREATED
    round_id = res_round.data["id"]

    # 3. Schedule candidate slot
    slot_payload = {
        "student_id": str(candidate.id),
        "scheduled_time": (timezone.now() + timezone.timedelta(days=10, hours=2)).isoformat(),
        "meeting_url": "https://meet.google.com/xyz-abc-def",
    }
    res_slot = client.post(f"/api/v1/interviews/rounds/{round_id}/schedule/", slot_payload, format="json")
    assert res_slot.status_code == status.HTTP_201_CREATED
    slot_id = res_slot.data["id"]

    # 4. Record attendance & round outcome
    outcome_payload = {
        "attendance_status": "PRESENT",
        "outcome": "SELECTED",
        "evaluator_notes": "Solved dynamic programming problem efficiently; strong algorithmic rigor.",
    }
    res_outcome = client.patch(f"/api/v1/interviews/slots/{slot_id}/outcome/", outcome_payload, format="json")
    assert res_outcome.status_code == status.HTTP_200_OK
    assert res_outcome.data["attendance_status"] == "PRESENT"
    assert res_outcome.data["outcome"] == "SELECTED"

