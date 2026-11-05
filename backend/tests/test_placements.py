"""Integration tests for Placement Offers & Joining Verification (MOD-009)."""
from decimal import Decimal
import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import RoleCatalog
from apps.accounts.services import create_user, assign_role
from apps.crm.services import create_company
from apps.jobs.services import create_job_requirement
from apps.students.models import StudentProfile, PlacementStatusChoices
from apps.placements.models import PlacementOffer, OfferStatusChoices, JoiningStatusChoices
from apps.placements.services import (
    create_placement_offer,
    record_offer_decision,
    verify_joining_status,
)


@pytest.fixture
def head_user(db):
    user = create_user(email="head_plc@gqt.local", password="Password@123")
    assign_role(user, RoleCatalog.PLACEMENT_HEAD)
    return user


@pytest.fixture
def sample_job(db, head_user):
    company = create_company(name="Microsoft Corporation", user=head_user)
    job = create_job_requirement(
        company=company,
        title="Support Engineer",
        description="Azure infrastructure support.",
        role_category="PRODUCT_SUPPORT",
        work_arrangement="HYBRID",
        min_cgpa=Decimal("7.00"),
        eligible_batches=["2025"],
        eligible_branches=["CSE", "IT"],
        max_backlogs_allowed=0,
        min_ctc_lpa=Decimal("11.00"),
        max_ctc_lpa=Decimal("14.00"),
        registration_deadline=timezone.now() + timezone.timedelta(days=7),
        user=head_user,
    )
    return job


@pytest.fixture
def candidate(db):
    return StudentProfile.objects.create(
        roll_number="GQT-OFFER-001",
        full_name="Kiran Reddy",
        email="kiran@gqt.local",
        phone="+919876543022",
        degree="B.Tech",
        branch="CSE",
        graduation_year=2025,
        cgpa=Decimal("8.90"),
        backlogs_count=0,
        placement_status=PlacementStatusChoices.SEEKING,
    )


@pytest.mark.django_db
def test_offer_issuance_acceptance_syncs_student_placement_status(sample_job, candidate, head_user):
    assert candidate.placement_status == PlacementStatusChoices.SEEKING

    # 1. Issue Offer
    offer = create_placement_offer(
        job=sample_job,
        student=candidate,
        designation="Support Engineer I",
        ctc_lpa=Decimal("12.50"),
        response_deadline=timezone.now().date() + timezone.timedelta(days=14),
        user=head_user,
    )
    assert offer.status == OfferStatusChoices.OFFER_ISSUED

    # 2. Candidate accepts offer -> student status automatically transitions to PLACED
    accepted_offer = record_offer_decision(
        offer=offer,
        decision=OfferStatusChoices.ACCEPTED,
        user=head_user,
    )
    assert accepted_offer.status == OfferStatusChoices.ACCEPTED
    candidate.refresh_from_db()
    assert candidate.placement_status == PlacementStatusChoices.PLACED

    # 3. Post-joining verification
    verified_offer = verify_joining_status(
        offer=accepted_offer,
        joining_status=JoiningStatusChoices.JOINED,
        user=head_user,
        actual_date=timezone.now().date(),
        notes="Verified joining onboarding with HR email confirmation.",
    )
    assert verified_offer.joining_status == JoiningStatusChoices.JOINED
    assert verified_offer.verified_by == head_user


@pytest.mark.django_db
def test_declined_offer_leaves_candidate_seeking(sample_job, candidate, head_user):
    offer = create_placement_offer(
        job=sample_job,
        student=candidate,
        designation="Support Engineer I",
        ctc_lpa=Decimal("12.50"),
        response_deadline=timezone.now().date() + timezone.timedelta(days=14),
        user=head_user,
    )
    declined_offer = record_offer_decision(
        offer=offer,
        decision=OfferStatusChoices.DECLINED,
        user=head_user,
        decline_reason="Pursuing higher studies (MS).",
    )
    assert declined_offer.status == OfferStatusChoices.DECLINED
    candidate.refresh_from_db()
    assert candidate.placement_status == PlacementStatusChoices.SEEKING

