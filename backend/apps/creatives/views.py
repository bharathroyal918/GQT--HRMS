"""Presentation and HTTP ViewSet Layer for Recruitment Creative Studio.

Provides versioned REST API endpoints for:
1. Creative requisitions management and workflow transitions.
2. Deliverable asset version uploads with multi-part streaming.
3. 4-point design compliance check evaluation.
4. Segregated review approvals and change requests.
5. Authenticated private asset downloads with nosniff security headers.
6. Operational queues (Triage, Designer, Review, Handoff) and KPI metrics.
"""
from typing import Any
from django.db import IntegrityError
from django.http import FileResponse, Http404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets, generics, serializers
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError as DRFValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, inline_serializer

from apps.creatives import selectors, services
from apps.creatives.models import CreativeRequest, CreativeAssetVersion
from apps.creatives.permissions import (
    IsCreativeStaffOrReadOnly,
    CanCreateCreativeRequest,
    CanTriageOrAssignCreative,
    CanReviewOrApproveCreative,
)
from apps.creatives.serializers import (
    CreativeRequestListSerializer,
    CreativeRequestDetailSerializer,
    CreateCreativeRequestSerializer,
    UpdateCreativeRequestSerializer,
    AssignDesignerSerializer,
    UploadVersionSerializer,
    CreativeAssetVersionDetailSerializer,
    DesignComplianceCheckSerializer,
    EvaluateCheckSerializer,
    ApproveVersionSerializer,
    RequestChangesSerializer,
    CancelRequestSerializer,
)


class CreativeRequestViewSet(viewsets.ModelViewSet):
    """Manage recruitment creative marketing requisitions."""

    permission_classes = [IsCreativeStaffOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    queryset = CreativeRequest.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return CreativeRequestListSerializer
        if self.action == "create":
            return CreateCreativeRequestSerializer
        if self.action in ["update", "partial_update"]:
            return UpdateCreativeRequestSerializer
        return CreativeRequestDetailSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CreativeRequest.objects.none()
        if not hasattr(self, "request") or not hasattr(self.request, "user"):
            return CreativeRequest.objects.all()
        return selectors.list_creative_requests(
            self.request.user,
            status=self.request.query_params.get("status"),
            priority=self.request.query_params.get("priority"),
            creative_type=self.request.query_params.get("creative_type"),
            assigned_to=self.request.query_params.get("assigned_to"),
            search=self.request.query_params.get("search"),
        )

    def retrieve(self, request, *args, **kwargs):
        req = selectors.get_creative_request_by_id(kwargs["pk"])
        if not req:
            raise Http404("Creative requisition not found.")
        serializer = CreativeRequestDetailSerializer(req)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = CreateCreativeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            req = services.create_creative_request(
                request.user,
                **serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(getattr(exc, "message_dict", exc.messages))

        output = CreativeRequestDetailSerializer(req)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        serializer = UpdateCreativeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            req = services.update_creative_request(
                request.user,
                kwargs["pk"],
                **serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(getattr(exc, "message_dict", exc.messages))

        output = CreativeRequestDetailSerializer(req)
        return Response(output.data)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Direct deletion of requisitions is prohibited. Use the cancel action."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        """Submit draft requisition for design triage."""
        try:
            req = services.submit_creative_request(request.user, pk)
        except DjangoValidationError as exc:
            raise DRFValidationError(getattr(exc, "message_dict", exc.messages))
        return Response(CreativeRequestDetailSerializer(req).data)

    @action(detail=True, methods=["post"], permission_classes=[CanTriageOrAssignCreative])
    def assign(self, request, pk=None):
        """Triage and assign requisition to a graphic designer."""
        serializer = AssignDesignerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            req = services.triage_and_assign_request(
                request.user,
                pk,
                **serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(getattr(exc, "message_dict", exc.messages))
        return Response(CreativeRequestDetailSerializer(req).data)

    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[IsAuthenticated],
    )
    def upload_version(self, request, pk=None):
        """Upload a new design asset deliverable version."""
        serializer = UploadVersionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            version = services.upload_asset_version(
                request.user,
                pk,
                uploaded_file=serializer.validated_data["file"],
                designer_notes=serializer.validated_data.get("designer_notes"),
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(getattr(exc, "message_dict", exc.messages))
        except IntegrityError:
            raise DRFValidationError(
                {"detail": "A version creation conflict occurred for this requisition. Please retry."}
            )

        return Response(
            CreativeAssetVersionDetailSerializer(version).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], permission_classes=[CanReviewOrApproveCreative])
    def handoff(self, request, pk=None):
        """Mark approved requisition ready for campus drive collateral."""
        notes = request.data.get("notes")
        try:
            req = services.mark_ready_for_handoff(request.user, pk, notes=notes)
        except DjangoValidationError as exc:
            raise DRFValidationError(getattr(exc, "message_dict", exc.messages))
        return Response(CreativeRequestDetailSerializer(req).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """Cancel requisition with documented justification."""
        serializer = CancelRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            req = services.cancel_creative_request(
                request.user,
                pk,
                cancellation_reason=serializer.validated_data["cancellation_reason"],
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(getattr(exc, "message_dict", exc.messages))
        return Response(CreativeRequestDetailSerializer(req).data)


class CreativeVersionViewSet(viewsets.GenericViewSet):
    """Manage asset version reviews, compliance checks, and secure downloads."""

    permission_classes = [IsCreativeStaffOrReadOnly]
    serializer_class = CreativeAssetVersionDetailSerializer
    queryset = CreativeAssetVersion.objects.all()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CreativeAssetVersion.objects.none()
        return CreativeAssetVersion.objects.all()

    @extend_schema(
        summary="Retrieve Asset Version Detail",
        responses={200: CreativeAssetVersionDetailSerializer},
    )
    def retrieve(self, request, pk=None):
        version = selectors.get_asset_version_by_id(pk)
        if not version:
            raise Http404("Asset version not found.")
        return Response(CreativeAssetVersionDetailSerializer(version).data)

    @extend_schema(
        summary="Evaluate Design Compliance Check",
        parameters=[
            OpenApiParameter("check_type", OpenApiTypes.STR, location=OpenApiParameter.PATH, description="Design compliance check type"),
        ],
        request=EvaluateCheckSerializer,
        responses={200: DesignComplianceCheckSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        url_path=r"checks/(?P<check_type>[^/.]+)",
        permission_classes=[CanReviewOrApproveCreative],
    )
    def evaluate_check(self, request, pk=None, check_type=None):
        """Evaluate a specific compliance check (PASSED/FLAGGED)."""
        serializer = EvaluateCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            check = services.evaluate_compliance_check(
                request.user,
                pk,
                check_type,
                status=serializer.validated_data["status"],
                notes=serializer.validated_data.get("notes"),
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(getattr(exc, "message_dict", exc.messages))
        return Response(DesignComplianceCheckSerializer(check).data)

    @extend_schema(
        summary="Approve Deliverable Asset Version",
        request=ApproveVersionSerializer,
        responses={200: CreativeAssetVersionDetailSerializer},
    )
    @action(detail=True, methods=["post"], permission_classes=[CanReviewOrApproveCreative])
    def approve(self, request, pk=None):
        """Authorize asset version. Enforces SoD and all 4 checks PASSED."""
        serializer = ApproveVersionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            version = services.approve_asset_version(
                request.user,
                pk,
                review_feedback=serializer.validated_data.get("review_feedback"),
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(getattr(exc, "message_dict", exc.messages))
        return Response(CreativeAssetVersionDetailSerializer(version).data)

    @extend_schema(
        summary="Request Changes on Asset Version",
        request=RequestChangesSerializer,
        responses={200: CreativeAssetVersionDetailSerializer},
    )
    @action(detail=True, methods=["post"], permission_classes=[CanReviewOrApproveCreative])
    def request_changes(self, request, pk=None):
        """Request revisions from designer with required feedback."""
        serializer = RequestChangesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            version = services.request_changes_on_version(
                request.user,
                pk,
                review_feedback=serializer.validated_data["review_feedback"],
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(getattr(exc, "message_dict", exc.messages))
        return Response(CreativeAssetVersionDetailSerializer(version).data)

    @extend_schema(
        summary="Securely Download Asset Version File",
        responses={200: bytes},
    )
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def download(self, request, pk=None):
        """Stream validated asset file with nosniff and defensive headers."""
        version = selectors.get_asset_version_by_id(pk)
        if not version:
            raise Http404("Asset version not found.")

        if not version.file:
            raise Http404("Asset file attachment is missing from storage.")

        as_attachment = request.query_params.get("download", "").lower() in ("true", "1")
        # Hardened defense: PDFs are strictly forced as attachments to prevent browser execution
        is_pdf = version.mime_type == "application/pdf" or version.original_filename.lower().endswith(".pdf")
        disposition = "attachment" if (as_attachment or is_pdf) else "inline"

        # Sanitize filename for header
        safe_filename = version.original_filename.replace('"', "").replace("\r", "").replace("\n", "")

        response = FileResponse(version.file.open("rb"), content_type=version.mime_type)
        response["Content-Disposition"] = f'{disposition}; filename="{safe_filename}"'
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Security-Policy"] = "default-src 'none'; sandbox"
        response["Cache-Control"] = "private, no-cache, no-store, must-revalidate"
        return response


class CreativeTriageQueueView(generics.ListAPIView):
    """Requisitions in SUBMITTED state awaiting designer assignment."""

    permission_classes = [CanTriageOrAssignCreative]
    serializer_class = CreativeRequestListSerializer

    def get_queryset(self):
        return selectors.list_triage_queue()


class CreativeDesignerQueueView(generics.ListAPIView):
    """Requisitions actively assigned to the authenticated designer."""

    permission_classes = [IsAuthenticated]
    serializer_class = CreativeRequestListSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not hasattr(self.request, "user") or not self.request.user.is_authenticated:
            return CreativeRequest.objects.none()
        return selectors.list_designer_queue(self.request.user)


class CreativeReviewQueueView(generics.ListAPIView):
    """Asset versions currently in review awaiting compliance evaluation."""

    permission_classes = [CanReviewOrApproveCreative]
    serializer_class = CreativeAssetVersionDetailSerializer

    def get_queryset(self):
        return selectors.list_review_queue()


class CreativeHandoffQueueView(generics.ListAPIView):
    """Approved requisitions ready for campus drive collateral distribution."""

    permission_classes = [CanReviewOrApproveCreative]
    serializer_class = CreativeRequestListSerializer

    def get_queryset(self):
        return selectors.list_handoff_queue()


class CreativeStudioMetricsView(APIView):
    """Creative Studio analytics and throughput KPI aggregations."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Creative Studio Analytics & Throughput Metrics",
        responses={
            200: inline_serializer(
                "CreativeStudioMetricsResponse",
                fields={
                    "total_requests": serializers.IntegerField(),
                    "triage_queue_count": serializers.IntegerField(),
                    "in_design_count": serializers.IntegerField(),
                    "in_review_count": serializers.IntegerField(),
                    "approved_count": serializers.IntegerField(),
                    "ready_for_handoff_count": serializers.IntegerField(),
                    "total_asset_versions": serializers.IntegerField(),
                    "pending_versions_review": serializers.IntegerField(),
                },
            )
        },
    )
    def get(self, request):
        metrics = selectors.get_creative_studio_metrics()
        return Response(metrics)

