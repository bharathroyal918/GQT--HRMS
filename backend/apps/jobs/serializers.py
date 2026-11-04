"""Serializers for Job Requirements, Verification Checks, and Workflow Queues."""
from decimal import Decimal
from rest_framework import serializers
from apps.accounts.models import User
from apps.crm.models import Company
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


class JobVerificationCheckSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual 5-point verification checks."""

    verified_by_name = serializers.SerializerMethodField()
    verified_by_email = serializers.SerializerMethodField()

    class Meta:
        model = JobVerificationCheck
        fields = [
            "id",
            "check_type",
            "status",
            "verified_by",
            "verified_by_name",
            "verified_by_email",
            "verified_at",
            "notes",
            "evidence_reference",
            "requires_reverification",
            "invalidation_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "check_type",
            "verified_by",
            "verified_by_name",
            "verified_by_email",
            "verified_at",
            "requires_reverification",
            "invalidation_reason",
            "created_at",
            "updated_at",
        ]

    def get_verified_by_name(self, obj) -> str:
        return obj.verified_by.full_name if obj.verified_by else ""

    def get_verified_by_email(self, obj) -> str:
        return obj.verified_by.email if obj.verified_by else ""


class JobVerificationCheckUpdateSerializer(serializers.Serializer):
    """Payload serializer for recording a reviewer check evaluation."""

    status = serializers.ChoiceField(choices=CheckStatusChoices.choices)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    evidence_reference = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        status = attrs.get("status")
        notes = attrs.get("notes", "").strip()
        if status in [CheckStatusChoices.FLAGGED, CheckStatusChoices.REJECTED] and not notes:
            raise serializers.ValidationError({"notes": "Meaningful reviewer notes are required when flagging or rejecting a check."})
        return attrs


class JobWorkflowHistorySerializer(serializers.ModelSerializer):
    """Read-only audit record serializer for state transitions and review decisions."""

    actor_name = serializers.SerializerMethodField()
    actor_email = serializers.SerializerMethodField()

    class Meta:
        model = JobWorkflowHistory
        fields = [
            "id",
            "from_status",
            "to_status",
            "actor",
            "actor_name",
            "actor_email",
            "action",
            "notes",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj) -> str:
        return obj.actor.full_name if obj.actor else "System"

    def get_actor_email(self, obj) -> str:
        return obj.actor.email if obj.actor else ""


class JobRequirementListSerializer(serializers.ModelSerializer):
    """Concise representation for tabular directory listings and search results."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    company_canonical_domain = serializers.CharField(source="company.canonical_domain", read_only=True)
    submitted_by_name = serializers.SerializerMethodField()
    assigned_verifier_name = serializers.SerializerMethodField()
    verification_summary = serializers.SerializerMethodField()

    class Meta:
        model = JobRequirement
        fields = [
            "id",
            "company",
            "company_name",
            "company_canonical_domain",
            "title",
            "role_category",
            "job_location",
            "work_arrangement",
            "min_ctc_lpa",
            "max_ctc_lpa",
            "vacancies_count",
            "registration_deadline",
            "interview_date",
            "status",
            "revision_number",
            "submitted_by",
            "submitted_by_name",
            "assigned_verifier",
            "assigned_verifier_name",
            "verification_summary",
            "created_at",
            "updated_at",
        ]

    def get_submitted_by_name(self, obj) -> str:
        return obj.submitted_by.full_name if obj.submitted_by else ""

    def get_assigned_verifier_name(self, obj) -> str:
        return obj.assigned_verifier.full_name if obj.assigned_verifier else ""

    def get_verification_summary(self, obj) -> dict:
        return obj.verification_summary


class JobRequirementDetailSerializer(serializers.ModelSerializer):
    """Comprehensive representation with embedded verification checks and audit history."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    company_canonical_domain = serializers.CharField(source="company.canonical_domain", read_only=True)
    company_industry = serializers.CharField(source="company.industry", read_only=True)
    submitted_by_name = serializers.SerializerMethodField()
    submitted_by_email = serializers.SerializerMethodField()
    assigned_verifier_name = serializers.SerializerMethodField()
    assigned_verifier_email = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    rejected_by_name = serializers.SerializerMethodField()
    verification_checks = JobVerificationCheckSerializer(many=True, read_only=True)
    workflow_history = JobWorkflowHistorySerializer(many=True, read_only=True)
    verification_summary = serializers.SerializerMethodField()
    is_all_checks_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = JobRequirement
        fields = [
            "id",
            "company",
            "company_name",
            "company_canonical_domain",
            "company_industry",
            "title",
            "description",
            "role_category",
            "required_skills",
            "min_cgpa",
            "min_percentage",
            "eligible_batches",
            "eligible_branches",
            "max_backlogs_allowed",
            "min_ctc_lpa",
            "max_ctc_lpa",
            "stipend_amount",
            "salary_details",
            "job_location",
            "work_arrangement",
            "has_bond",
            "bond_duration_months",
            "bond_details",
            "interview_rounds",
            "interview_process_notes",
            "interview_date",
            "registration_deadline",
            "vacancies_count",
            "submitted_by",
            "submitted_by_name",
            "submitted_by_email",
            "assigned_verifier",
            "assigned_verifier_name",
            "assigned_verifier_email",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "rejected_by",
            "rejected_by_name",
            "rejected_at",
            "rejection_reason",
            "changes_requested_reason",
            "status",
            "revision_number",
            "verification_checks",
            "workflow_history",
            "verification_summary",
            "is_all_checks_verified",
            "created_at",
            "updated_at",
        ]

    def get_submitted_by_name(self, obj) -> str:
        return obj.submitted_by.full_name if obj.submitted_by else ""

    def get_submitted_by_email(self, obj) -> str:
        return obj.submitted_by.email if obj.submitted_by else ""

    def get_assigned_verifier_name(self, obj) -> str:
        return obj.assigned_verifier.full_name if obj.assigned_verifier else ""

    def get_assigned_verifier_email(self, obj) -> str:
        return obj.assigned_verifier.email if obj.assigned_verifier else ""

    def get_approved_by_name(self, obj) -> str:
        return obj.approved_by.full_name if obj.approved_by else ""

    def get_rejected_by_name(self, obj) -> str:
        return obj.rejected_by.full_name if obj.rejected_by else ""

    def get_verification_summary(self, obj) -> dict:
        return obj.verification_summary


class JobRequirementCreateUpdateSerializer(serializers.ModelSerializer):
    """Payload serializer for job requirement creation and draft modification."""

    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())

    class Meta:
        model = JobRequirement
        fields = [
            "company",
            "title",
            "description",
            "role_category",
            "required_skills",
            "min_cgpa",
            "min_percentage",
            "eligible_batches",
            "eligible_branches",
            "max_backlogs_allowed",
            "min_ctc_lpa",
            "max_ctc_lpa",
            "stipend_amount",
            "salary_details",
            "job_location",
            "work_arrangement",
            "has_bond",
            "bond_duration_months",
            "bond_details",
            "interview_rounds",
            "interview_process_notes",
            "interview_date",
            "registration_deadline",
            "vacancies_count",
        ]

    def validate(self, attrs):
        min_ctc = attrs.get("min_ctc_lpa")
        max_ctc = attrs.get("max_ctc_lpa")
        if min_ctc is not None and max_ctc is not None:
            if min_ctc < Decimal("0.00") or max_ctc < Decimal("0.00"):
                raise serializers.ValidationError("CTC values cannot be negative.")
            if min_ctc > max_ctc:
                raise serializers.ValidationError({"max_ctc_lpa": "Maximum CTC must be greater than or equal to minimum CTC."})

        min_cgpa = attrs.get("min_cgpa")
        if min_cgpa is not None and (min_cgpa < Decimal("0.00") or min_cgpa > Decimal("10.00")):
            raise serializers.ValidationError({"min_cgpa": "Minimum CGPA must be between 0.00 and 10.00."})

        min_percentage = attrs.get("min_percentage")
        if min_percentage is not None and (min_percentage < Decimal("0.00") or min_percentage > Decimal("100.00")):
            raise serializers.ValidationError({"min_percentage": "Minimum percentage must be between 0.00 and 100.00."})

        has_bond = attrs.get("has_bond", False)
        bond_duration = attrs.get("bond_duration_months")
        if has_bond and (not bond_duration or bond_duration <= 0):
            raise serializers.ValidationError({"bond_duration_months": "Bond duration in months is required when a bond applies."})

        reg_deadline = attrs.get("registration_deadline")
        interview_date = attrs.get("interview_date")
        if interview_date and reg_deadline:
            if interview_date < reg_deadline.date():
                raise serializers.ValidationError({"interview_date": "Interview date cannot precede registration deadline."})

        return attrs


class JobWorkflowActionSerializer(serializers.Serializer):
    """Payload serializer for approval, rejection, and change request workflows."""

    reason = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class JobAssignVerifierSerializer(serializers.Serializer):
    """Payload serializer for delegating a job verification review."""

    verifier_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source="verifier",
    )


class JobAmendSerializer(serializers.Serializer):
    """Payload serializer for authorizing an amendment to an already approved job."""

    reason = serializers.CharField(required=True, min_length=10)
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    min_ctc_lpa = serializers.DecimalField(required=False, max_digits=6, decimal_places=2)
    max_ctc_lpa = serializers.DecimalField(required=False, max_digits=6, decimal_places=2)
    min_cgpa = serializers.DecimalField(required=False, max_digits=4, decimal_places=2, allow_null=True)
    min_percentage = serializers.DecimalField(required=False, max_digits=5, decimal_places=2, allow_null=True)
    registration_deadline = serializers.DateTimeField(required=False)
    interview_date = serializers.DateField(required=False, allow_null=True)
    vacancies_count = serializers.IntegerField(required=False, allow_null=True)
    required_skills = serializers.ListField(child=serializers.CharField(), required=False)
    eligible_batches = serializers.ListField(child=serializers.CharField(), required=False)
    eligible_branches = serializers.ListField(child=serializers.CharField(), required=False)
    job_location = serializers.CharField(required=False, allow_blank=True)
    work_arrangement = serializers.ChoiceField(choices=WorkArrangementChoices.choices, required=False)

