"""API Views for Student Preparation and Step 23 Gate (MOD-006)."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView
from drf_spectacular.utils import extend_schema

from apps.accounts.models import RoleCatalog
from apps.accounts.permissions import role_required, IsPlacementHead
from apps.core.pagination import StandardResultsSetPagination
from apps.jobs.models import JobRequirement
from apps.students.models import StudentProfile
from apps.preparation.models import (
    ResumeReview,
    AssessmentRecord,
    MockInterview,
    ReadinessCertification,
)
from apps.preparation.services import (
    evaluate_readiness_criteria,
    certify_student_readiness,
)
from apps.preparation.serializers import (
    ResumeReviewSerializer,
    AssessmentRecordSerializer,
    MockInterviewSerializer,
    ReadinessCertificationSerializer,
    CertifyReadinessRequestSerializer,
)


class ResumeReviewListCreateAPIView(ListCreateAPIView):
    """List and log trainer resume reviews."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.TRAINER,
        )
    ]
    serializer_class = ResumeReviewSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = ResumeReview.objects.select_related("student", "reviewer").order_by("-created_at")
        student_id = self.request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


class AssessmentRecordListCreateAPIView(ListCreateAPIView):
    """List and record aptitude, technical, or coding assessments."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.TRAINER,
        )
    ]
    serializer_class = AssessmentRecordSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = AssessmentRecord.objects.select_related("student").order_by("-conducted_at")
        student_id = self.request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs


class MockInterviewListCreateAPIView(ListCreateAPIView):
    """Schedule and record mock interview scorecards."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.TRAINER,
        )
    ]
    serializer_class = MockInterviewSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = MockInterview.objects.select_related("student", "interviewer").order_by("-scheduled_date")
        student_id = self.request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(interviewer=self.request.user)


class ReadinessStatusAPIView(APIView):
    """Inspect whether a student meets the 3 prerequisites for Step 23 certification."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.TRAINER,
        )
    ]

    def get(self, request):
        student_id = request.query_params.get("student_id")
        job_id = request.query_params.get("job_id")
        student = get_object_or_404(StudentProfile, id=student_id)
        job = get_object_or_404(JobRequirement, id=job_id)

        can_certify, missing = evaluate_readiness_criteria(student, job)
        is_already_certified = ReadinessCertification.objects.filter(
            student=student, job=job, is_certified=True
        ).exists()

        return Response(
            {
                "student_id": str(student.id),
                "job_id": str(job.id),
                "can_certify": can_certify,
                "missing_criteria": missing,
                "is_certified": is_already_certified,
            },
            status=status.HTTP_200_OK,
        )


class CertifyReadinessAPIView(APIView):
    """Execute Step 23 Placement Readiness Certification (Placement Head or Admin)."""

    permission_classes = [IsPlacementHead]

    @extend_schema(
        summary="Certify Placement Readiness (Step 23)",
        request=CertifyReadinessRequestSerializer,
        responses={200: ReadinessCertificationSerializer},
    )
    def post(self, request):
        serializer = CertifyReadinessRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = get_object_or_404(StudentProfile, id=serializer.validated_data["student_id"])
        job = get_object_or_404(JobRequirement, id=serializer.validated_data["job_id"])

        cert = certify_student_readiness(
            student=student,
            job=job,
            certified_by=request.user,
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(ReadinessCertificationSerializer(cert).data, status=status.HTTP_200_OK)

