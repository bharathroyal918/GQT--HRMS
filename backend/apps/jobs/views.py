"""Views and ViewSets for Job Requirements, Verification, and Approval Workflow."""
from rest_framework import viewsets, generics, views, status, permissions, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes, inline_serializer

from apps.core.pagination import StandardResultsSetPagination
from apps.jobs.models import JobRequirement, JobStatusChoices
from apps.jobs.permissions import (
    IsJobStaffOrReadOnly,
    CanVerifyJob,
    CanApproveOrRejectJob,
)
from apps.jobs import selectors, services
from apps.jobs.serializers import (
    JobRequirementListSerializer,
    JobRequirementDetailSerializer,
    JobRequirementCreateUpdateSerializer,
    JobVerificationCheckSerializer,
    JobVerificationCheckUpdateSerializer,
    JobWorkflowHistorySerializer,
    JobWorkflowActionSerializer,
    JobAssignVerifierSerializer,
    JobAmendSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="List and filter job requirements with pagination"),
    retrieve=extend_schema(summary="Retrieve detailed job requirement with checks and history"),
    create=extend_schema(summary="Create a new job requirement draft"),
    update=extend_schema(summary="Update job draft or changes-requested requirement"),
    partial_update=extend_schema(summary="Partially update job draft requirement"),
    destroy=extend_schema(summary="Delete a draft job requirement"),
)
class JobRequirementViewSet(viewsets.ModelViewSet):
    """ViewSet managing JobRequirement lifecycle, verification gates, and approvals."""

    pagination_class = StandardResultsSetPagination
    permission_classes = [IsJobStaffOrReadOnly]

    def get_queryset(self):
        return selectors.list_jobs(filters=self.request.query_params)

    def get_serializer_class(self):
        if self.action == "list":
            return JobRequirementListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return JobRequirementCreateUpdateSerializer
        return JobRequirementDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = services.create_job_requirement(
            user=request.user,
            **serializer.validated_data,
        )
        output_serializer = JobRequirementDetailSerializer(job)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        job = self.get_object()
        serializer = self.get_serializer(job, data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        updated_job = services.update_job_requirement(
            job=job,
            user=request.user,
            **serializer.validated_data,
        )
        output_serializer = JobRequirementDetailSerializer(updated_job)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        job = self.get_object()
        if job.status not in [JobStatusChoices.DRAFT, JobStatusChoices.REJECTED]:
            return Response(
                {"detail": f"Cannot delete job in '{job.status}' status. Only drafts or rejected jobs can be removed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Submit job requirement for 5-point verification review",
        request=None,
        responses={200: JobRequirementDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="submit")
    def submit_for_verification(self, request, pk=None):
        job = self.get_object()
        updated_job = services.submit_for_verification(job=job, user=request.user)
        return Response(JobRequirementDetailSerializer(updated_job).data)

    @extend_schema(
        summary="Assign a verifier to conduct the 5-point verification review",
        request=JobAssignVerifierSerializer,
        responses={200: JobRequirementDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="assign-verifier")
    def assign_verifier(self, request, pk=None):
        job = self.get_object()
        serializer = JobAssignVerifierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_job = services.assign_verifier(
            job=job,
            verifier=serializer.validated_data["verifier"],
            user=request.user,
        )
        return Response(JobRequirementDetailSerializer(updated_job).data)

    @extend_schema(
        summary="Request changes on a job requirement with mandatory feedback",
        request=JobWorkflowActionSerializer,
        responses={200: JobRequirementDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="request-changes")
    def request_changes(self, request, pk=None):
        job = self.get_object()
        serializer = JobWorkflowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason") or serializer.validated_data.get("notes")
        updated_job = services.request_changes(job=job, reason=reason, user=request.user)
        return Response(JobRequirementDetailSerializer(updated_job).data)

    @extend_schema(
        summary="Approve a verified job requirement (Segregation of Duties enforced)",
        request=JobWorkflowActionSerializer,
        responses={200: JobRequirementDetailSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="approve",
        permission_classes=[CanApproveOrRejectJob],
    )
    def approve(self, request, pk=None):
        job = self.get_object()
        self.check_object_permissions(request, job)
        serializer = JobWorkflowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notes = serializer.validated_data.get("notes", "")
        updated_job = services.approve_job(job=job, user=request.user, notes=notes)
        return Response(JobRequirementDetailSerializer(updated_job).data)

    @extend_schema(
        summary="Reject a job requirement with documented justification",
        request=JobWorkflowActionSerializer,
        responses={200: JobRequirementDetailSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="reject",
        permission_classes=[CanApproveOrRejectJob],
    )
    def reject(self, request, pk=None):
        job = self.get_object()
        self.check_object_permissions(request, job)
        serializer = JobWorkflowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason") or serializer.validated_data.get("notes")
        updated_job = services.reject_job(job=job, reason=reason, user=request.user)
        return Response(JobRequirementDetailSerializer(updated_job).data)

    @extend_schema(
        summary="Amend an already approved job requirement (creates new revision)",
        request=JobAmendSerializer,
        responses={200: JobRequirementDetailSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="amend",
        permission_classes=[CanApproveOrRejectJob],
    )
    def amend(self, request, pk=None):
        job = self.get_object()
        serializer = JobAmendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data.copy()
        reason = data.pop("reason")
        updated_job = services.amend_approved_job(
            job=job,
            reason=reason,
            user=request.user,
            **data,
        )
        return Response(JobRequirementDetailSerializer(updated_job).data)

    @extend_schema(
        summary="Retrieve all five verification checks for this job",
        responses={200: JobVerificationCheckSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="checks")
    def get_verification_checks(self, request, pk=None):
        job = self.get_object()
        checks = job.verification_checks.all().order_by("check_type")
        return Response(JobVerificationCheckSerializer(checks, many=True).data)

    @extend_schema(
        summary="Update a specific 5-point verification check evaluation",
        parameters=[
            OpenApiParameter("check_type", OpenApiTypes.STR, location=OpenApiParameter.PATH, description="Verification check type enum"),
        ],
        request=JobVerificationCheckUpdateSerializer,
        responses={200: JobVerificationCheckSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="checks/(?P<check_type>[^/.]+)",
        permission_classes=[CanVerifyJob],
    )
    def update_check(self, request, pk=None, check_type=None):
        job = self.get_object()
        serializer = JobVerificationCheckUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        check = services.update_verification_check(
            job=job,
            check_type=check_type,
            status=serializer.validated_data["status"],
            user=request.user,
            notes=serializer.validated_data.get("notes", ""),
            evidence_reference=serializer.validated_data.get("evidence_reference", ""),
        )
        return Response(JobVerificationCheckSerializer(check).data)

    @extend_schema(
        summary="Retrieve append-only workflow state history for this job",
        responses={200: JobWorkflowHistorySerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="history")
    def get_workflow_history(self, request, pk=None):
        job = self.get_object()
        history = job.workflow_history.all().order_by("-created_at")
        return Response(JobWorkflowHistorySerializer(history, many=True).data)


class JobVerificationQueueView(generics.ListAPIView):
    """Queue of jobs currently pending or undergoing 5-point verification review."""

    pagination_class = StandardResultsSetPagination
    permission_classes = [IsJobStaffOrReadOnly]
    serializer_class = JobRequirementListSerializer

    def get_queryset(self):
        return selectors.list_verification_queue()


class JobApprovalQueueView(generics.ListAPIView):
    """Queue of jobs that have passed all 5 checks and await Placement Head approval."""

    pagination_class = StandardResultsSetPagination
    permission_classes = [CanApproveOrRejectJob]
    serializer_class = JobRequirementListSerializer

    def get_queryset(self):
        return selectors.list_approval_queue()


class JobWorkflowMetricsView(views.APIView):
    """Real-time pipeline metrics and verification statistics based on persisted data."""

    permission_classes = [IsJobStaffOrReadOnly]

    @extend_schema(
        summary="Job Workflow & Verification Pipeline Metrics",
        responses={
            200: inline_serializer(
                "JobWorkflowMetricsResponse",
                fields={
                    "total_jobs": serializers.IntegerField(),
                    "draft_jobs": serializers.IntegerField(),
                    "pending_verification_jobs": serializers.IntegerField(),
                    "under_verification_jobs": serializers.IntegerField(),
                    "changes_requested_jobs": serializers.IntegerField(),
                    "pending_approval_jobs": serializers.IntegerField(),
                    "approved_jobs": serializers.IntegerField(),
                    "rejected_jobs": serializers.IntegerField(),
                    "verification_stats": inline_serializer(
                        "JobVerificationStatsResponse",
                        fields={
                            "total_checks": serializers.IntegerField(),
                            "verified_checks": serializers.IntegerField(),
                            "pending_checks": serializers.IntegerField(),
                            "flagged_checks": serializers.IntegerField(),
                            "rejected_checks": serializers.IntegerField(),
                        },
                    ),
                },
            )
        },
    )
    def get(self, request):
        metrics = selectors.get_job_workflow_metrics()
        return Response(metrics, status=status.HTTP_200_OK)

