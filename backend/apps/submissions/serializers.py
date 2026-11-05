"""Serializers for Candidate Submissions & Dispatch (MOD-007)."""
from rest_framework import serializers
from apps.submissions.models import SubmissionPackage, SubmissionItem, DispatchLog


class SubmissionItemSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(source="student.roll_number", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    branch = serializers.CharField(source="student.branch", read_only=True)
    cgpa = serializers.DecimalField(source="student.cgpa", max_digits=4, decimal_places=2, read_only=True)

    class Meta:
        model = SubmissionItem
        fields = [
            "id",
            "student",
            "student_roll",
            "student_name",
            "branch",
            "cgpa",
            "resume_version",
            "is_shortlisted",
            "created_at",
        ]


class DispatchLogSerializer(serializers.ModelSerializer):
    dispatched_by_name = serializers.CharField(source="dispatched_by.full_name", read_only=True)

    class Meta:
        model = DispatchLog
        fields = [
            "id",
            "channel",
            "recipient_email",
            "recipient_name",
            "dispatched_by",
            "dispatched_by_name",
            "dispatched_at",
            "notes",
        ]


class SubmissionPackageListSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)
    candidates_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = SubmissionPackage
        fields = [
            "id",
            "package_code",
            "title",
            "job",
            "job_title",
            "company_name",
            "status",
            "candidates_count",
            "roster_hash",
            "dispatched_at",
            "acknowledged_at",
            "created_at",
        ]


class SubmissionPackageDetailSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)
    items = SubmissionItemSerializer(many=True, read_only=True)
    dispatch_logs = DispatchLogSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.full_name", read_only=True)

    class Meta:
        model = SubmissionPackage
        fields = [
            "id",
            "package_code",
            "title",
            "job",
            "job_title",
            "company_name",
            "status",
            "roster_hash",
            "created_by",
            "created_by_name",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "dispatched_at",
            "acknowledged_at",
            "notes",
            "items",
            "dispatch_logs",
            "created_at",
        ]


class CreateSubmissionPackageSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True)


class AddCandidateSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()


class DispatchPackageSerializer(serializers.Serializer):
    recipient_email = serializers.EmailField()
    recipient_name = serializers.CharField(max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True)

