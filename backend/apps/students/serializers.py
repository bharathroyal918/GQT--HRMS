"""Serializers for Student Placement Operations & Eligibility Engine (MOD-005)."""
from rest_framework import serializers
from apps.students.models import (
    StudentProfile,
    StudentResume,
    DriveRegistration,
    EligibilityEvaluation,
    CandidateCohort,
)


class StudentResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentResume
        fields = [
            "id",
            "version",
            "file_name",
            "file_hash",
            "file_size_bytes",
            "is_verified",
            "verified_at",
            "created_at",
        ]
        read_only_fields = fields


class StudentProfileListSerializer(serializers.ModelSerializer):
    latest_resume_version = serializers.SerializerMethodField()
    is_resume_verified = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "roll_number",
            "full_name",
            "email",
            "phone",
            "degree",
            "branch",
            "graduation_year",
            "cgpa",
            "backlogs_count",
            "placement_status",
            "is_active",
            "latest_resume_version",
            "is_resume_verified",
            "created_at",
        ]

    def get_latest_resume_version(self, obj: StudentProfile):
        resumes = obj.resumes.all()
        return resumes[0].version if resumes else None

    def get_is_resume_verified(self, obj: StudentProfile):
        resumes = obj.resumes.all()
        return resumes[0].is_verified if resumes else False


class StudentProfileDetailSerializer(serializers.ModelSerializer):
    resumes = StudentResumeSerializer(many=True, read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "roll_number",
            "full_name",
            "email",
            "phone",
            "degree",
            "branch",
            "graduation_year",
            "cgpa",
            "backlogs_count",
            "tenth_percentage",
            "twelfth_percentage",
            "skills",
            "placement_status",
            "is_active",
            "notes",
            "resumes",
            "created_at",
            "updated_at",
        ]


class EligibilityEvaluationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)
    overridden_by_name = serializers.CharField(source="overridden_by.full_name", read_only=True)

    class Meta:
        model = EligibilityEvaluation
        fields = [
            "id",
            "student",
            "job",
            "job_title",
            "company_name",
            "is_eligible",
            "failed_criteria",
            "evaluated_at",
            "manually_overridden",
            "overridden_by_name",
            "override_reason",
        ]
        read_only_fields = fields


class DriveRegistrationSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(source="student.roll_number", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)

    class Meta:
        model = DriveRegistration
        fields = [
            "id",
            "student",
            "student_roll",
            "student_name",
            "job",
            "job_title",
            "company_name",
            "status",
            "registered_at",
        ]
        read_only_fields = ["id", "registered_at"]


class CandidateCohortSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)
    students_count = serializers.IntegerField(source="students.count", read_only=True)

    class Meta:
        model = CandidateCohort
        fields = [
            "id",
            "job",
            "job_title",
            "company_name",
            "status",
            "students_count",
            "finalized_at",
            "created_at",
        ]
        read_only_fields = fields


class EligibilityCheckRequestSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    job_id = serializers.UUIDField()


class EligibilityOverrideRequestSerializer(serializers.Serializer):
    evaluation_id = serializers.UUIDField()
    reason = serializers.CharField(min_length=10)
