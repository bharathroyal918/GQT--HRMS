"""Recruitment CRM REST Serializers."""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.accounts.serializers import UserProfileSerializer
from apps.crm.models import (
    Company,
    HRContact,
    OutreachActivity,
    FollowUp,
    IndustryChoices,
    AcquisitionSourceChoices,
    CompanyStatusChoices,
    CompanyTierChoices,
    PreferredChannelChoices,
    ContactStatusChoices,
    OutreachChannelChoices,
    OutreachOutcomeChoices,
    FollowUpPriorityChoices,
    FollowUpStatusChoices,
)


class DuplicateCheckInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    website = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    exclude_company_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class HRContactSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = HRContact
        fields = [
            "id",
            "company",
            "company_name",
            "name",
            "designation",
            "department",
            "email",
            "phone",
            "alternate_phone",
            "linkedin_url",
            "preferred_channel",
            "status",
            "is_primary",
            "notes",
            "assigned_to",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class HRContactCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HRContact
        fields = [
            "name",
            "designation",
            "department",
            "email",
            "phone",
            "alternate_phone",
            "linkedin_url",
            "preferred_channel",
            "status",
            "is_primary",
            "notes",
            "assigned_to",
        ]


class OutreachActivitySerializer(serializers.ModelSerializer):
    executive_name = serializers.CharField(source="executive.full_name", read_only=True)
    contact_name = serializers.CharField(source="contact.name", read_only=True, default=None)
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = OutreachActivity
        fields = [
            "id",
            "company",
            "company_name",
            "contact",
            "contact_name",
            "executive",
            "executive_name",
            "attempted_at",
            "channel",
            "outcome",
            "notes",
            "next_action",
            "follow_up_date",
            "created_at",
        ]
        read_only_fields = ["id", "executive", "created_at"]


class OutreachActivityCreateSerializer(serializers.Serializer):
    contact_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    channel = serializers.ChoiceField(choices=OutreachChannelChoices.choices)
    outcome = serializers.ChoiceField(choices=OutreachOutcomeChoices.choices)
    notes = serializers.CharField(min_length=1)
    next_action = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    follow_up_date = serializers.DateTimeField(required=False, allow_null=True, default=None)


class FollowUpSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    contact_name = serializers.CharField(source="contact.name", read_only=True, default=None)
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    is_due_today = serializers.BooleanField(read_only=True)

    class Meta:
        model = FollowUp
        fields = [
            "id",
            "company",
            "company_name",
            "contact",
            "contact_name",
            "outreach_activity",
            "assigned_to",
            "assigned_to_name",
            "title",
            "description",
            "due_date",
            "priority",
            "status",
            "is_overdue",
            "is_due_today",
            "completed_at",
            "completed_by",
            "cancellation_reason",
            "created_at",
        ]
        read_only_fields = ["id", "completed_at", "completed_by", "created_at"]


class FollowUpCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUp
        fields = [
            "company",
            "contact",
            "assigned_to",
            "title",
            "description",
            "due_date",
            "priority",
        ]


class FollowUpCompleteSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class FollowUpCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=3)


class CompanyListSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True, default=None)
    contacts_count = serializers.IntegerField(read_only=True, default=0)
    outreach_count = serializers.IntegerField(read_only=True, default=0)
    pending_followups_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "normalized_name",
            "website",
            "canonical_domain",
            "industry",
            "source",
            "status",
            "tier",
            "assigned_to",
            "assigned_to_name",
            "contacts_count",
            "outreach_count",
            "pending_followups_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "normalized_name", "canonical_domain", "created_at", "updated_at"]


class CompanyDetailSerializer(serializers.ModelSerializer):
    assigned_to = UserProfileSerializer(read_only=True)
    contacts = HRContactSerializer(many=True, read_only=True)
    recent_outreach = serializers.SerializerMethodField()
    active_follow_ups = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "normalized_name",
            "website",
            "canonical_domain",
            "industry",
            "source",
            "status",
            "tier",
            "assigned_to",
            "notes",
            "contacts",
            "recent_outreach",
            "active_follow_ups",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "normalized_name", "canonical_domain", "created_at", "updated_at"]

    @extend_schema_field(OutreachActivitySerializer(many=True))
    def get_recent_outreach(self, obj):
        activities = obj.outreach_activities.filter(is_deleted=False).order_by("-attempted_at")[:10]
        return OutreachActivitySerializer(activities, many=True).data

    @extend_schema_field(FollowUpSerializer(many=True))
    def get_active_follow_ups(self, obj):
        follow_ups = obj.follow_ups.filter(
            status=FollowUpStatusChoices.PENDING, is_deleted=False
        ).order_by("due_date")[:10]
        return FollowUpSerializer(follow_ups, many=True).data


class CompanyCreateSerializer(serializers.ModelSerializer):
    allow_duplicate = serializers.BooleanField(required=False, default=False, write_only=True)

    class Meta:
        model = Company
        fields = [
            "name",
            "website",
            "industry",
            "source",
            "status",
            "tier",
            "assigned_to",
            "notes",
            "allow_duplicate",
        ]


class CompanyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "name",
            "website",
            "industry",
            "source",
            "status",
            "tier",
            "assigned_to",
            "notes",
        ]
