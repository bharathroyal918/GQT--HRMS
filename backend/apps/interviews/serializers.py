"""Serializers for Placement Drives & Multi-Round Interviews (MOD-008)."""
from rest_framework import serializers
from apps.interviews.models import PlacementDrive, InterviewRound, InterviewSlot


class InterviewSlotSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(source="student.roll_number", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    branch = serializers.CharField(source="student.branch", read_only=True)
    evaluated_by_name = serializers.CharField(source="evaluated_by.full_name", read_only=True)

    class Meta:
        model = InterviewSlot
        fields = [
            "id",
            "round",
            "student",
            "student_roll",
            "student_name",
            "branch",
            "scheduled_time",
            "meeting_url",
            "attendance_status",
            "evaluator_notes",
            "outcome",
            "evaluated_by",
            "evaluated_by_name",
            "evaluated_at",
            "created_at",
        ]


class InterviewRoundSerializer(serializers.ModelSerializer):
    slots = InterviewSlotSerializer(many=True, read_only=True)
    slots_count = serializers.IntegerField(source="slots.count", read_only=True)

    class Meta:
        model = InterviewRound
        fields = [
            "id",
            "drive",
            "round_number",
            "round_type",
            "round_name",
            "instructions",
            "slots_count",
            "slots",
            "created_at",
        ]


class PlacementDriveListSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)
    coordinator_name = serializers.CharField(source="coordinator.full_name", read_only=True)
    rounds_count = serializers.IntegerField(source="rounds.count", read_only=True)

    class Meta:
        model = PlacementDrive
        fields = [
            "id",
            "drive_code",
            "title",
            "job",
            "job_title",
            "company_name",
            "drive_date",
            "venue_or_link",
            "drive_mode",
            "status",
            "coordinator_name",
            "rounds_count",
            "created_at",
        ]


class PlacementDriveDetailSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)
    coordinator_name = serializers.CharField(source="coordinator.full_name", read_only=True)
    rounds = InterviewRoundSerializer(many=True, read_only=True)

    class Meta:
        model = PlacementDrive
        fields = [
            "id",
            "drive_code",
            "title",
            "job",
            "job_title",
            "company_name",
            "drive_date",
            "venue_or_link",
            "drive_mode",
            "status",
            "coordinator",
            "coordinator_name",
            "instructions",
            "rounds",
            "created_at",
            "updated_at",
        ]


class CreateDriveSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    drive_date = serializers.DateTimeField()
    venue_or_link = serializers.CharField(max_length=512)
    drive_mode = serializers.CharField(default="VIRTUAL")
    instructions = serializers.CharField(required=False, allow_blank=True)


class AddRoundSerializer(serializers.Serializer):
    round_number = serializers.IntegerField(min_value=1)
    round_type = serializers.CharField()
    round_name = serializers.CharField(max_length=128)
    instructions = serializers.CharField(required=False, allow_blank=True)


class ScheduleSlotSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    scheduled_time = serializers.DateTimeField()
    meeting_url = serializers.CharField(required=False, allow_blank=True)


class UpdateSlotOutcomeSerializer(serializers.Serializer):
    attendance_status = serializers.CharField(required=False)
    outcome = serializers.CharField(required=False)
    evaluator_notes = serializers.CharField(required=False, allow_blank=True)

