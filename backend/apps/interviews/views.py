"""API Views for Placement Drives & Multi-Round Interviews (MOD-008)."""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from drf_spectacular.utils import extend_schema

from apps.accounts.models import RoleCatalog
from apps.accounts.permissions import role_required
from apps.core.models import AuditLog
from apps.core.pagination import StandardResultsSetPagination
from apps.jobs.models import JobRequirement
from apps.students.models import StudentProfile
from apps.interviews.models import PlacementDrive, InterviewRound, InterviewSlot
from apps.interviews.serializers import (
    PlacementDriveListSerializer,
    PlacementDriveDetailSerializer,
    InterviewRoundSerializer,
    InterviewSlotSerializer,
    CreateDriveSerializer,
    AddRoundSerializer,
    ScheduleSlotSerializer,
    UpdateSlotOutcomeSerializer,
)


def generate_drive_code() -> str:
    current_year = timezone.now().year
    count = PlacementDrive.objects.filter(created_at__year=current_year).count() + 1
    return f"DRV-{current_year}-{count:03d}"


class PlacementDriveListCreateAPIView(APIView):
    """List placement drives or schedule a new drive."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.INTERVIEW_COORDINATOR,
            RoleCatalog.AUDITOR,
        )
    ]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        qs = (
            PlacementDrive.objects.select_related("job", "job__company", "coordinator")
            .prefetch_related("rounds")
            .order_by("-drive_date")
        )
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        if page is not None:
            serializer = PlacementDriveListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = PlacementDriveListSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreateDriveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = get_object_or_404(JobRequirement, id=serializer.validated_data["job_id"])
        code = generate_drive_code()

        drive = PlacementDrive.objects.create(
            job=job,
            drive_code=code,
            title=serializer.validated_data["title"],
            drive_date=serializer.validated_data["drive_date"],
            venue_or_link=serializer.validated_data["venue_or_link"],
            drive_mode=serializer.validated_data.get("drive_mode", "VIRTUAL"),
            instructions=serializer.validated_data.get("instructions", ""),
            coordinator=request.user,
        )

        AuditLog.objects.create(
            user=request.user,
            action="PLACEMENT_DRIVE_SCHEDULED",
            resource_type="PlacementDrive",
            resource_id=str(drive.id),
            changes={"drive_code": code, "job": job.title},
        )

        return Response(PlacementDriveDetailSerializer(drive).data, status=status.HTTP_201_CREATED)


class PlacementDriveDetailAPIView(RetrieveAPIView):
    """Retrieve full placement drive details, rounds, and candidate schedule slots."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.INTERVIEW_COORDINATOR,
            RoleCatalog.AUDITOR,
        )
    ]
    serializer_class = PlacementDriveDetailSerializer
    queryset = (
        PlacementDrive.objects.select_related("job", "job__company", "coordinator")
        .prefetch_related("rounds", "rounds__slots", "rounds__slots__student")
    )
    lookup_field = "id"


class InterviewRoundCreateAPIView(APIView):
    """Add a structured interview round (e.g. Coding, Technical, HR) to a placement drive."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.INTERVIEW_COORDINATOR,
        )
    ]

    def post(self, request, drive_id):
        drive = get_object_or_404(PlacementDrive, id=drive_id)
        serializer = AddRoundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        round_obj = InterviewRound.objects.create(
            drive=drive,
            round_number=serializer.validated_data["round_number"],
            round_type=serializer.validated_data["round_type"],
            round_name=serializer.validated_data["round_name"],
            instructions=serializer.validated_data.get("instructions", ""),
        )

        return Response(InterviewRoundSerializer(round_obj).data, status=status.HTTP_201_CREATED)


class InterviewSlotScheduleAPIView(APIView):
    """Schedule a candidate for an interview round."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.INTERVIEW_COORDINATOR,
        )
    ]

    def post(self, request, round_id):
        round_obj = get_object_or_404(InterviewRound, id=round_id)
        serializer = ScheduleSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = get_object_or_404(StudentProfile, id=serializer.validated_data["student_id"])

        slot, _ = InterviewSlot.objects.update_or_create(
            round=round_obj,
            student=student,
            defaults={
                "scheduled_time": serializer.validated_data["scheduled_time"],
                "meeting_url": serializer.validated_data.get("meeting_url", ""),
            },
        )

        return Response(InterviewSlotSerializer(slot).data, status=status.HTTP_201_CREATED)


class InterviewSlotOutcomeUpdateAPIView(APIView):
    """Record candidate attendance and round outcome (SELECTED, NEXT_ROUND, etc.)."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.INTERVIEW_COORDINATOR,
        )
    ]

    def patch(self, request, slot_id):
        slot = get_object_or_404(InterviewSlot, id=slot_id)
        serializer = UpdateSlotOutcomeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if "attendance_status" in serializer.validated_data:
            slot.attendance_status = serializer.validated_data["attendance_status"]
        if "outcome" in serializer.validated_data:
            slot.outcome = serializer.validated_data["outcome"]
            slot.evaluated_by = request.user
            slot.evaluated_at = timezone.now()
        if "evaluator_notes" in serializer.validated_data:
            slot.evaluator_notes = serializer.validated_data["evaluator_notes"]

        slot.save()

        AuditLog.objects.create(
            user=request.user,
            action="INTERVIEW_ROUND_OUTCOME_LOGGED",
            resource_type="InterviewSlot",
            resource_id=str(slot.id),
            changes={
                "student": slot.student.roll_number,
                "attendance": slot.attendance_status,
                "outcome": slot.outcome,
            },
        )

        return Response(InterviewSlotSerializer(slot).data, status=status.HTTP_200_OK)

