"""Serializers for Offers & Placement Management (MOD-009)."""
from rest_framework import serializers
from apps.placements.models import PlacementOffer


class PlacementOfferSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(source="student.roll_number", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    branch = serializers.CharField(source="student.branch", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    verified_by_name = serializers.CharField(source="verified_by.full_name", read_only=True)

    class Meta:
        model = PlacementOffer
        fields = [
            "id",
            "job",
            "job_title",
            "company_name",
            "student",
            "student_roll",
            "student_name",
            "branch",
            "designation",
            "ctc_lpa",
            "offer_date",
            "response_deadline",
            "offer_letter_name",
            "status",
            "decision_date",
            "decline_reason",
            "joining_status",
            "expected_joining_date",
            "actual_joining_date",
            "joining_notes",
            "verified_by_name",
            "verified_at",
            "created_at",
        ]


class CreatePlacementOfferSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    student_id = serializers.UUIDField()
    designation = serializers.CharField(max_length=128)
    ctc_lpa = serializers.DecimalField(max_digits=6, decimal_places=2)
    response_deadline = serializers.DateField()
    offer_letter_name = serializers.CharField(required=False, allow_blank=True)


class RecordDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["ACCEPTED", "DECLINED"])
    decline_reason = serializers.CharField(required=False, allow_blank=True)


class VerifyJoiningSerializer(serializers.Serializer):
    joining_status = serializers.ChoiceField(choices=["JOINED", "NOT_JOINED", "DEFERRED", "AWAITING_JOINING"])
    actual_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)

