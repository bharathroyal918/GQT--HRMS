"""Placement Management, Offers & Joining Verification Models (MOD-009)."""
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class OfferStatusChoices(models.TextChoices):
    OFFER_ISSUED = "OFFER_ISSUED", "Offer Letter Issued"
    ACCEPTED = "ACCEPTED", "Accepted by Candidate"
    DECLINED = "DECLINED", "Declined by Candidate"
    EXPIRED = "EXPIRED", "Offer Expired"


class JoiningStatusChoices(models.TextChoices):
    AWAITING_JOINING = "AWAITING_JOINING", "Awaiting Joining Date"
    JOINED = "JOINED", "Successfully Joined"
    NOT_JOINED = "NOT_JOINED", "Did Not Join"
    DEFERRED = "DEFERRED", "Joining Deferred"


class PlacementOffer(TimeStampedModel):
    """Authoritative corporate offer issued to a candidate with tracking through to joining."""

    job = models.ForeignKey(
        "jobs.JobRequirement",
        on_delete=models.CASCADE,
        related_name="offers",
    )
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="placement_offers",
    )
    designation = models.CharField(max_length=128)
    ctc_lpa = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Offered compensation in Lakhs Per Annum (LPA)",
    )
    offer_date = models.DateField(default=timezone.now)
    response_deadline = models.DateField()
    offer_letter_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=32,
        choices=OfferStatusChoices.choices,
        default=OfferStatusChoices.OFFER_ISSUED,
        db_index=True,
    )
    decision_date = models.DateTimeField(null=True, blank=True)
    decline_reason = models.TextField(blank=True)

    # Post-offer joining audit
    joining_status = models.CharField(
        max_length=32,
        choices=JoiningStatusChoices.choices,
        default=JoiningStatusChoices.AWAITING_JOINING,
        db_index=True,
    )
    expected_joining_date = models.DateField(null=True, blank=True)
    actual_joining_date = models.DateField(null=True, blank=True)
    joining_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_joinings",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "placements_offer"
        ordering = ["-offer_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "student"],
                name="unique_offer_per_candidate_job",
            )
        ]

    def __str__(self) -> str:
        return f"{self.student.roll_number} - {self.designation} at {self.job.company.name} ({self.status})"

