"""API Views for Student Management and Eligibility Engine (MOD-005)."""
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    ListAPIView,
)
from drf_spectacular.utils import extend_schema

from apps.accounts.models import RoleCatalog
from apps.accounts.permissions import role_required, IsPlacementHead
from apps.core.pagination import StandardResultsSetPagination
from apps.jobs.models import JobRequirement
from apps.students.models import (
    StudentProfile,
    StudentResume,
    DriveRegistration,
    EligibilityEvaluation,
    CandidateCohort,
)
from apps.students.selectors import list_students, get_student_metrics
from apps.students.services import (
    evaluate_student_eligibility,
    register_student_for_job,
    override_student_eligibility,
    finalize_candidate_cohort,
)
from apps.students.serializers import (
    StudentProfileListSerializer,
    StudentProfileDetailSerializer,
    StudentResumeSerializer,
    EligibilityEvaluationSerializer,
    DriveRegistrationSerializer,
    CandidateCohortSerializer,
    EligibilityCheckRequestSerializer,
    EligibilityOverrideRequestSerializer,
)


class StudentListCreateAPIView(APIView):
    """List student profiles with filtering, or create a new student."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.TRAINER,
            RoleCatalog.AUDITOR,
        )
    ]
    pagination_class = StandardResultsSetPagination

    @extend_schema(summary="List Students", responses={200: StudentProfileListSerializer(many=True)})
    def get(self, request):
        search = request.query_params.get("search")
        branch = request.query_params.get("branch")
        grad_year = request.query_params.get("graduation_year")
        placement_status = request.query_params.get("placement_status")
        is_active = request.query_params.get("is_active")

        year_int = int(grad_year) if grad_year and grad_year.isdigit() else None
        active_bool = None
        if is_active is not None:
            active_bool = is_active.lower() in ("true", "1")

        qs = list_students(
            search=search,
            branch=branch,
            graduation_year=year_int,
            placement_status=placement_status,
            is_active=active_bool,
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        if page is not None:
            serializer = StudentProfileListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = StudentProfileListSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(summary="Create Student", responses={201: StudentProfileDetailSerializer})
    def post(self, request):
        serializer = StudentProfileDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()
        return Response(StudentProfileDetailSerializer(student).data, status=status.HTTP_201_CREATED)


class StudentDetailAPIView(RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or soft-delete a student profile."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.TRAINER,
            RoleCatalog.AUDITOR,
        )
    ]
    serializer_class = StudentProfileDetailSerializer
    queryset = StudentProfile.objects.prefetch_related("resumes")
    lookup_field = "id"


class StudentMetricsAPIView(APIView):
    """High-level student placement statistics and branch breakdown."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.TRAINER,
            RoleCatalog.AUDITOR,
        )
    ]

    def get(self, request):
        data = get_student_metrics()
        return Response(data, status=status.HTTP_200_OK)


class EligibilityCheckAPIView(APIView):
    """Execute deterministic eligibility verification on a candidate against a job."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.TRAINER,
        )
    ]

    @extend_schema(
        summary="Evaluate Eligibility",
        request=EligibilityCheckRequestSerializer,
        responses={200: EligibilityEvaluationSerializer},
    )
    def post(self, request):
        serializer = EligibilityCheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = get_object_or_404(StudentProfile, id=serializer.validated_data["student_id"])
        job = get_object_or_404(JobRequirement, id=serializer.validated_data["job_id"])

        is_eligible, failed_reasons, evaluation = evaluate_student_eligibility(student, job)
        return Response(EligibilityEvaluationSerializer(evaluation).data, status=status.HTTP_200_OK)


class EligibilityOverrideAPIView(APIView):
    """Authorize manual eligibility override (Admin or Placement Head)."""

    permission_classes = [IsPlacementHead]

    @extend_schema(
        summary="Authorize Eligibility Override",
        request=EligibilityOverrideRequestSerializer,
        responses={200: EligibilityEvaluationSerializer},
    )
    def post(self, request):
        serializer = EligibilityOverrideRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        evaluation = get_object_or_404(EligibilityEvaluation, id=serializer.validated_data["evaluation_id"])
        updated = override_student_eligibility(
            evaluation=evaluation,
            overridden_by=request.user,
            reason=serializer.validated_data["reason"],
        )
        return Response(EligibilityEvaluationSerializer(updated).data, status=status.HTTP_200_OK)


class DriveRegistrationListCreateAPIView(ListCreateAPIView):
    """List or register students for recruitment drives."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
        )
    ]
    serializer_class = DriveRegistrationSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = DriveRegistration.objects.select_related("student", "job", "job__company").order_by("-registered_at")
        job_id = self.request.query_params.get("job_id")
        student_id = self.request.query_params.get("student_id")
        if job_id:
            qs = qs.filter(job_id=job_id)
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    def create(self, request, *args, **kwargs):
        student_id = request.data.get("student")
        job_id = request.data.get("job")

        student = get_object_or_404(StudentProfile, id=student_id)
        job = get_object_or_404(JobRequirement, id=job_id)

        registration = register_student_for_job(student=student, job=job, user=request.user)
        return Response(DriveRegistrationSerializer(registration).data, status=status.HTTP_201_CREATED)


class CandidateCohortFinalizeAPIView(APIView):
    """Finalize candidate cohort for a job requirement."""

    permission_classes = [IsPlacementHead]

    def post(self, request, job_id):
        job = get_object_or_404(JobRequirement, id=job_id)
        cohort = finalize_candidate_cohort(job=job, user=request.user)
        return Response(CandidateCohortSerializer(cohort).data, status=status.HTTP_200_OK)

