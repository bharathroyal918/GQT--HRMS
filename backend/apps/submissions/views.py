"""API Views for Candidate Submissions & Recruiter Profile Dispatch (MOD-007)."""
import csv
import io
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from drf_spectacular.utils import extend_schema

from apps.accounts.models import RoleCatalog
from apps.accounts.permissions import role_required, IsPlacementHead
from apps.core.pagination import StandardResultsSetPagination
from apps.core.views import _sanitize_csv_cell
from apps.jobs.models import JobRequirement
from apps.students.models import StudentProfile
from apps.submissions.models import SubmissionPackage, SubmissionItem
from apps.submissions.services import (
    create_submission_package,
    add_candidate_to_package,
    approve_submission_package,
    dispatch_submission_package,
    acknowledge_submission_package,
)
from apps.submissions.serializers import (
    SubmissionPackageListSerializer,
    SubmissionPackageDetailSerializer,
    SubmissionItemSerializer,
    CreateSubmissionPackageSerializer,
    AddCandidateSerializer,
    DispatchPackageSerializer,
)


class SubmissionPackageListCreateAPIView(APIView):
    """List submission packages or create a new draft package."""

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
            SubmissionPackage.objects.select_related("job", "job__company")
            .prefetch_related("items")
            .order_by("-created_at")
        )
        job_id = request.query_params.get("job_id")
        if job_id:
            qs = qs.filter(job_id=job_id)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        if page is not None:
            serializer = SubmissionPackageListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SubmissionPackageListSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreateSubmissionPackageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = get_object_or_404(JobRequirement, id=serializer.validated_data["job_id"])
        package = create_submission_package(
            job=job,
            title=serializer.validated_data["title"],
            user=request.user,
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(SubmissionPackageDetailSerializer(package).data, status=status.HTTP_201_CREATED)


class SubmissionPackageDetailAPIView(RetrieveAPIView):
    """Retrieve complete submission package manifest with candidate roster and dispatch logs."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.AUDITOR,
        )
    ]
    serializer_class = SubmissionPackageDetailSerializer
    queryset = (
        SubmissionPackage.objects.select_related("job", "job__company", "created_by", "approved_by")
        .prefetch_related("items", "items__student", "dispatch_logs")
    )
    lookup_field = "id"


class SubmissionPackageAddCandidateAPIView(APIView):
    """Attach candidate to package (strictly enforces Step 23 Placement Readiness Gate)."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
        )
    ]

    def post(self, request, id):
        package = get_object_or_404(SubmissionPackage, id=id)
        serializer = AddCandidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = get_object_or_404(StudentProfile, id=serializer.validated_data["student_id"])
        item = add_candidate_to_package(package=package, student=student, user=request.user)

        return Response(SubmissionItemSerializer(item).data, status=status.HTTP_201_CREATED)


class SubmissionPackageApproveAPIView(APIView):
    """Placement Head approval for candidate profile package."""

    permission_classes = [IsPlacementHead]

    def post(self, request, id):
        package = get_object_or_404(SubmissionPackage, id=id)
        approved = approve_submission_package(package=package, user=request.user)
        return Response(SubmissionPackageDetailSerializer(approved).data, status=status.HTTP_200_OK)


class SubmissionPackageDispatchAPIView(APIView):
    """Execute profile dispatch to corporate partner HR contact."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
        )
    ]

    def post(self, request, id):
        package = get_object_or_404(SubmissionPackage, id=id)
        serializer = DispatchPackageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dispatch_log = dispatch_submission_package(
            package=package,
            recipient_email=serializer.validated_data["recipient_email"],
            recipient_name=serializer.validated_data["recipient_name"],
            user=request.user,
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(SubmissionPackageDetailSerializer(package).data, status=status.HTTP_200_OK)


class SubmissionPackageAcknowledgeAPIView(APIView):
    """Record recruiter receipt and acknowledgement of candidate dispatch."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
        )
    ]

    def post(self, request, id):
        package = get_object_or_404(SubmissionPackage, id=id)
        notes = request.data.get("notes", "")
        updated = acknowledge_submission_package(package=package, user=request.user, notes=notes)
        return Response(SubmissionPackageDetailSerializer(updated).data, status=status.HTTP_200_OK)


class SubmissionPackageRosterCSVAPIView(APIView):
    """Export formula-sanitized Master Candidate Roster spreadsheet."""

    permission_classes = [
        role_required(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.AUDITOR,
        )
    ]

    def get(self, request, id):
        package = get_object_or_404(SubmissionPackage.objects.prefetch_related("items__student"), id=id)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Roll Number",
            "Student Full Name",
            "Degree",
            "Branch",
            "Graduation Year",
            "CGPA",
            "Email",
            "Phone",
            "Resume Version",
            "Shortlisted",
        ])

        for item in package.items.all():
            st = item.student
            writer.writerow([
                _sanitize_csv_cell(st.roll_number),
                _sanitize_csv_cell(st.full_name),
                _sanitize_csv_cell(st.degree),
                _sanitize_csv_cell(st.branch),
                _sanitize_csv_cell(st.graduation_year),
                _sanitize_csv_cell(st.cgpa),
                _sanitize_csv_cell(st.email),
                _sanitize_csv_cell(st.phone),
                _sanitize_csv_cell(f"v{item.resume_version}"),
                _sanitize_csv_cell("YES" if item.is_shortlisted else "NO"),
            ])

        response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
        filename = f"roster_{package.package_code.lower().replace('-', '_')}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

