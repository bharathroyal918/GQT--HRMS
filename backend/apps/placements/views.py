"""API Views for Placement Offers and Joining Verification (MOD-009)."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from drf_spectacular.utils import extend_schema

from apps.accounts.models import RoleCatalog
from apps.accounts.permissions import role_required, IsPlacementHead
from apps.core.pagination import StandardResultsSetPagination
from apps.jobs.models import JobRequirement
from apps.students.models import StudentProfile
from apps.placements.models import PlacementOffer
from apps.placements.services import (
    create_placement_offer,
    record_offer_decision,
    verify_joining_status,
)
from apps.placements.serializers import (
    PlacementOfferSerializer,
    CreatePlacementOfferSerializer,
    RecordDecisionSerializer,
    VerifyJoiningSerializer,
)


class PlacementOfferListCreateAPIView(APIView):
    """List placement offers or record an authoritative job offer."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.AUDITOR,
        )
    ]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        qs = (
            PlacementOffer.objects.select_related("job", "job__company", "student", "verified_by")
            .order_by("-offer_date")
        )
        status_filter = request.query_params.get("status")
        student_id = request.query_params.get("student_id")
        job_id = request.query_params.get("job_id")

        if status_filter:
            qs = qs.filter(status=status_filter)
        if student_id:
            qs = qs.filter(student_id=student_id)
        if job_id:
            qs = qs.filter(job_id=job_id)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        if page is not None:
            serializer = PlacementOfferSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = PlacementOfferSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreatePlacementOfferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = get_object_or_404(JobRequirement, id=serializer.validated_data["job_id"])
        student = get_object_or_404(StudentProfile, id=serializer.validated_data["student_id"])

        offer = create_placement_offer(
            job=job,
            student=student,
            designation=serializer.validated_data["designation"],
            ctc_lpa=serializer.validated_data["ctc_lpa"],
            response_deadline=serializer.validated_data["response_deadline"],
            user=request.user,
            offer_letter_name=serializer.validated_data.get("offer_letter_name", ""),
        )
        return Response(PlacementOfferSerializer(offer).data, status=status.HTTP_201_CREATED)


class PlacementOfferDetailAPIView(RetrieveAPIView):
    """Retrieve full placement offer details and audit status."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.AUDITOR,
        )
    ]
    serializer_class = PlacementOfferSerializer
    queryset = PlacementOffer.objects.select_related("job", "job__company", "student", "verified_by")
    lookup_field = "id"


class PlacementOfferDecisionAPIView(APIView):
    """Record student offer acceptance or decline decision."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
        )
    ]

    def post(self, request, id):
        offer = get_object_or_404(PlacementOffer, id=id)
        serializer = RecordDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = record_offer_decision(
            offer=offer,
            decision=serializer.validated_data["decision"],
            user=request.user,
            decline_reason=serializer.validated_data.get("decline_reason", ""),
        )
        return Response(PlacementOfferSerializer(updated).data, status=status.HTTP_200_OK)


class PlacementOfferJoiningVerifyAPIView(APIView):
    """Verify and audit student joining status."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
        )
    ]

    def post(self, request, id):
        offer = get_object_or_404(PlacementOffer, id=id)
        serializer = VerifyJoiningSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = verify_joining_status(
            offer=offer,
            joining_status=serializer.validated_data["joining_status"],
            user=request.user,
            actual_date=serializer.validated_data.get("actual_date"),
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(PlacementOfferSerializer(updated).data, status=status.HTTP_200_OK)

