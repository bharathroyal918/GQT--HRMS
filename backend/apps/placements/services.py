"""Domain Services for Offers, Candidate Acceptance & Joining Verification (MOD-009)."""
from datetime import date
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.jobs.models import JobRequirement
from apps.students.models import StudentProfile, PlacementStatusChoices
from apps.placements.models import (
    PlacementOffer,
    OfferStatusChoices,
    JoiningStatusChoices,
)


@transaction.atomic
def create_placement_offer(
    *,
    job: JobRequirement,
    student: StudentProfile,
    designation: str,
    ctc_lpa: Decimal,
    response_deadline: date,
    user: User,
    offer_letter_name: str = "",
) -> PlacementOffer:
    """Create a new formal placement offer for a candidate."""
    offer = PlacementOffer.objects.create(
        job=job,
        student=student,
        designation=designation.strip(),
        ctc_lpa=ctc_lpa,
        response_deadline=response_deadline,
        offer_letter_name=offer_letter_name.strip(),
        status=OfferStatusChoices.OFFER_ISSUED,
    )

    AuditLog.objects.create(
        user=user,
        action="PLACEMENT_OFFER_ISSUED",
        resource_type="PlacementOffer",
        resource_id=str(offer.id),
        changes={
            "student": student.roll_number,
            "company": job.company.name,
            "ctc_lpa": str(ctc_lpa),
        },
    )

    return offer


@transaction.atomic
def record_offer_decision(
    *,
    offer: PlacementOffer,
    decision: str,
    user: User,
    decline_reason: str = "",
) -> PlacementOffer:
    """Record candidate offer acceptance or decline, automatically syncing placement pool state."""
    if decision not in (OfferStatusChoices.ACCEPTED, OfferStatusChoices.DECLINED):
        raise ValidationError(f"Invalid offer decision '{decision}'. Must be ACCEPTED or DECLINED.")

    offer.status = decision
    offer.decision_date = timezone.now()
    if decision == OfferStatusChoices.DECLINED:
        offer.decline_reason = decline_reason.strip()
    offer.save()

    # Automatic student status sync
    student = offer.student
    if decision == OfferStatusChoices.ACCEPTED:
        student.placement_status = PlacementStatusChoices.PLACED
        student.save()
    elif decision == OfferStatusChoices.DECLINED:
        # If student has no other accepted offers, remain SEEKING
        has_other_accepted = PlacementOffer.objects.filter(
            student=student, status=OfferStatusChoices.ACCEPTED
        ).exclude(id=offer.id).exists()
        if not has_other_accepted:
            student.placement_status = PlacementStatusChoices.SEEKING
            student.save()

    AuditLog.objects.create(
        user=user,
        action="OFFER_DECISION_RECORDED",
        resource_type="PlacementOffer",
        resource_id=str(offer.id),
        changes={
            "student": student.roll_number,
            "decision": decision,
            "student_placement_status": student.placement_status,
        },
    )

    return offer


@transaction.atomic
def verify_joining_status(
    *,
    offer: PlacementOffer,
    joining_status: str,
    user: User,
    actual_date: date = None,
    notes: str = "",
) -> PlacementOffer:
    """Audit joining outcome; if NOT_JOINED, automatically restores candidate to active placement pool."""
    if joining_status not in JoiningStatusChoices.values:
        raise ValidationError(f"Invalid joining status '{joining_status}'.")

    offer.joining_status = joining_status
    offer.actual_joining_date = actual_date
    offer.joining_notes = notes.strip()
    offer.verified_by = user
    offer.verified_at = timezone.now()
    offer.save()

    student = offer.student
    if joining_status == JoiningStatusChoices.NOT_JOINED:
        # Candidate did not join; restore to placement pool
        student.placement_status = PlacementStatusChoices.SEEKING
        student.save()

    AuditLog.objects.create(
        user=user,
        action="JOINING_STATUS_VERIFIED",
        resource_type="PlacementOffer",
        resource_id=str(offer.id),
        changes={
            "student": student.roll_number,
            "joining_status": joining_status,
            "student_placement_status": student.placement_status,
        },
    )

    return offer

