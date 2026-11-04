"""DRF Serializers for Creative Studio Domain."""
from rest_framework import serializers
from apps.creatives.models import (
    CreativeRequest,
    CreativeAssetVersion,
    DesignComplianceCheck,
    CreativeWorkflowHistory,
    CreativeStatusChoices,
    CreativeTypeChoices,
    AspectRatioChoices,
    DeliverableFormatChoices,
    CreativePriorityChoices,
    VersionStatusChoices,
    ComplianceCheckTypeChoices,
    ComplianceCheckStatusChoices,
)


class DesignComplianceCheckSerializer(serializers.ModelSerializer):
    check_type_display = serializers.CharField(
        source="get_check_type_display", read_only=True
    )
    verified_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DesignComplianceCheck
        fields = [
            "id",
            "check_type",
            "check_type_display",
            "status",
            "notes",
            "verified_by",
            "verified_by_name",
            "verified_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_verified_by_name(self, obj) -> str:
        if not obj.verified_by:
            return ""
        return obj.verified_by.full_name or obj.verified_by.email


class CreativeAssetVersionDetailSerializer(serializers.ModelSerializer):
    uploader_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    compliance_checks = DesignComplianceCheckSerializer(many=True, read_only=True)
    all_checks_passed = serializers.SerializerMethodField()

    class Meta:
        model = CreativeAssetVersion
        fields = [
            "id",
            "version_number",
            "original_filename",
            "file_size_bytes",
            "mime_type",
            "sha256_hash",
            "width",
            "height",
            "designer_notes",
            "status",
            "uploader",
            "uploader_name",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "review_feedback",
            "compliance_checks",
            "all_checks_passed",
            "created_at",
        ]
        read_only_fields = fields

    def get_uploader_name(self, obj) -> str:
        if not obj.uploader:
            return ""
        return obj.uploader.full_name or obj.uploader.email

    def get_reviewed_by_name(self, obj) -> str:
        if not obj.reviewed_by:
            return ""
        return obj.reviewed_by.full_name or obj.reviewed_by.email

    def get_all_checks_passed(self, obj) -> bool:
        checks = list(obj.compliance_checks.all())
        return len(checks) == 4 and all(
            c.status == ComplianceCheckStatusChoices.PASSED for c in checks
        )


class CreativeWorkflowHistorySerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = CreativeWorkflowHistory
        fields = [
            "id",
            "from_status",
            "to_status",
            "actor",
            "actor_name",
            "action",
            "notes",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj) -> str:
        if not obj.actor:
            return "System"
        return obj.actor.full_name or obj.actor.email


class CreativeRequestListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company.name", read_only=True, default=""
    )
    job_title = serializers.CharField(
        source="job_requirement.title", read_only=True, default=""
    )
    created_by_name = serializers.SerializerMethodField()
    assigned_designer_name = serializers.SerializerMethodField()
    active_version_number = serializers.SerializerMethodField()
    versions_count = serializers.SerializerMethodField()

    class Meta:
        model = CreativeRequest
        fields = [
            "id",
            "request_code",
            "title",
            "creative_type",
            "aspect_ratio",
            "deliverable_format",
            "priority",
            "status",
            "target_completion_date",
            "job_requirement",
            "job_title",
            "company",
            "company_name",
            "created_by",
            "created_by_name",
            "assigned_designer",
            "assigned_designer_name",
            "active_version_number",
            "versions_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj) -> str:
        if not obj.created_by:
            return ""
        return obj.created_by.full_name or obj.created_by.email

    def get_assigned_designer_name(self, obj) -> str:
        if not obj.assigned_designer:
            return "Unassigned"
        return obj.assigned_designer.full_name or obj.assigned_designer.email

    def get_active_version_number(self, obj) -> int | None:
        if obj.active_version:
            return obj.active_version.version_number
        return None

    def get_versions_count(self, obj) -> int:
        return obj.versions.count()


class CreativeRequestDetailSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company.name", read_only=True, default=""
    )
    job_title = serializers.CharField(
        source="job_requirement.title", read_only=True, default=""
    )
    created_by_name = serializers.SerializerMethodField()
    assigned_designer_name = serializers.SerializerMethodField()
    active_version = CreativeAssetVersionDetailSerializer(read_only=True)
    versions = CreativeAssetVersionDetailSerializer(many=True, read_only=True)
    history = CreativeWorkflowHistorySerializer(many=True, read_only=True)

    class Meta:
        model = CreativeRequest
        fields = [
            "id",
            "request_code",
            "title",
            "creative_type",
            "aspect_ratio",
            "deliverable_format",
            "brief",
            "priority",
            "status",
            "target_completion_date",
            "cancellation_reason",
            "job_requirement",
            "job_title",
            "company",
            "company_name",
            "created_by",
            "created_by_name",
            "assigned_designer",
            "assigned_designer_name",
            "active_version",
            "versions",
            "history",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj) -> str:
        if not obj.created_by:
            return ""
        return obj.created_by.full_name or obj.created_by.email

    def get_assigned_designer_name(self, obj) -> str:
        if not obj.assigned_designer:
            return "Unassigned"
        return obj.assigned_designer.full_name or obj.assigned_designer.email


class CreateCreativeRequestSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    brief = serializers.CharField()
    creative_type = serializers.ChoiceField(
        choices=CreativeTypeChoices.choices, default=CreativeTypeChoices.JOB_FLYER
    )
    aspect_ratio = serializers.ChoiceField(
        choices=AspectRatioChoices.choices, default=AspectRatioChoices.SQUARE
    )
    deliverable_format = serializers.ChoiceField(
        choices=DeliverableFormatChoices.choices, default=DeliverableFormatChoices.PNG
    )
    priority = serializers.ChoiceField(
        choices=CreativePriorityChoices.choices, default=CreativePriorityChoices.MEDIUM
    )
    target_completion_date = serializers.DateField(required=False, allow_null=True)
    job_requirement_id = serializers.UUIDField(required=False, allow_null=True)
    company_id = serializers.UUIDField(required=False, allow_null=True)


class UpdateCreativeRequestSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    brief = serializers.CharField(required=False)
    creative_type = serializers.ChoiceField(
        choices=CreativeTypeChoices.choices, required=False
    )
    aspect_ratio = serializers.ChoiceField(
        choices=AspectRatioChoices.choices, required=False
    )
    deliverable_format = serializers.ChoiceField(
        choices=DeliverableFormatChoices.choices, required=False
    )
    priority = serializers.ChoiceField(
        choices=CreativePriorityChoices.choices, required=False
    )
    target_completion_date = serializers.DateField(required=False, allow_null=True)


class AssignDesignerSerializer(serializers.Serializer):
    assigned_designer_id = serializers.UUIDField()
    priority = serializers.ChoiceField(
        choices=CreativePriorityChoices.choices, required=False
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class UploadVersionSerializer(serializers.Serializer):
    file = serializers.FileField()
    designer_notes = serializers.CharField(required=False, allow_blank=True)


class EvaluateCheckSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ComplianceCheckStatusChoices.choices)
    notes = serializers.CharField(required=False, allow_blank=True)


class ApproveVersionSerializer(serializers.Serializer):
    review_feedback = serializers.CharField(required=False, allow_blank=True)


class RequestChangesSerializer(serializers.Serializer):
    review_feedback = serializers.CharField()


class CancelRequestSerializer(serializers.Serializer):
    cancellation_reason = serializers.CharField()

