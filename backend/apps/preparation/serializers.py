"""Serializers for Student Preparation & Readiness (MOD-006)."""
from rest_framework import serializers
from apps.preparation.models import (
    ResumeReview,
    AssessmentRecord,
    MockInterview,
    ReadinessCertification,
)


class ResumeReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.full_name", read_only=True)
    student_roll = serializers.CharField(source="student.roll_number", read_only=True)

    class Meta:
        model = ResumeReview
        fields = [
            "id",
            "student",
            "student_roll",
            "job",
            "reviewer",
            "reviewer_name",
            "score",
            "status",
            "notes",
            "created_at",
        ]


class AssessmentRecordSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(source="student.roll_number", read_only=True)

    class Meta:
        model = AssessmentRecord
        fields = [
            "id",
            "student",
            "student_roll",
            "job",
            "test_type",
            "score",
            "max_score",
            "pass_threshold",
            "is_passed",
            "conducted_at",
        ]


class MockInterviewSerializer(serializers.ModelSerializer):
    interviewer_name = serializers.CharField(source="interviewer.full_name", read_only=True)
    student_roll = serializers.CharField(source="student.roll_number", read_only=True)

    class Meta:
        model = MockInterview
        fields = [
            "id",
            "student",
            "student_roll",
            "job",
            "interviewer",
            "interviewer_name",
            "scheduled_date",
            "conducted_date",
            "status",
            "technical_score",
            "communication_score",
            "problem_solving_score",
            "aggregate_score",
            "feedback",
            "is_recommended",
        ]


class ReadinessCertificationSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(source="student.roll_number", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    certified_by_name = serializers.CharField(source="certified_by.full_name", read_only=True)

    class Meta:
        model = ReadinessCertification
        fields = [
            "id",
            "student",
            "student_roll",
            "job",
            "job_title",
            "is_certified",
            "certified_by",
            "certified_by_name",
            "certified_at",
            "certification_notes",
        ]
        read_only_fields = fields


class CertifyReadinessRequestSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    job_id = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True)
