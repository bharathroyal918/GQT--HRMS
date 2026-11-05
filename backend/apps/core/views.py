"""Core Infrastructure Views: Health, Readiness, and Diagnostics."""
import csv
import io
import json
from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from apps.accounts.models import RoleCatalog
from apps.accounts.permissions import role_required
from apps.core.models import AuditLog
from apps.core.pagination import StandardResultsSetPagination
from apps.core.selectors import list_audit_logs, get_audit_summary
from apps.core.serializers import AuditLogSerializer, AuditSummarySerializer


class HealthCheckAPIView(APIView):
    """Liveness probe confirming the web application process is responsive."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Service Liveness Probe",
        description="Public health check confirming the application is online. Exposes no secrets.",
        responses={
            200: inline_serializer(
                name="HealthCheckResponse",
                fields={
                    "status": serializers.CharField(),
                    "environment": serializers.CharField(),
                    "version": serializers.CharField(),
                },
            )
        },
    )
    def get(self, request):
        return Response(
            {
                "status": "healthy",
                "environment": getattr(settings, "ENVIRONMENT", "development"),
                "version": "1.0.0",
            },
            status=status.HTTP_200_OK,
        )


class ReadinessAPIView(APIView):
    """Readiness probe verifying database connectivity and essential subsystems."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Service Readiness Probe",
        description="Verifies database responsiveness before routing live traffic.",
        responses={
            200: inline_serializer(
                name="ReadinessResponse",
                fields={
                    "status": serializers.CharField(),
                    "database": serializers.CharField(),
                },
            ),
            503: inline_serializer(
                name="ReadinessErrorResponse",
                fields={
                    "status": serializers.CharField(),
                    "database": serializers.CharField(),
                    "detail": serializers.CharField(),
                },
            ),
        },
    )
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            db_status = "connected"
            http_status = status.HTTP_200_OK
        except Exception as exc:
            db_status = "unavailable"
            return Response(
                {
                    "status": "not_ready",
                    "database": db_status,
                    "detail": "Database connectivity check failed.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "status": "ready",
                "database": db_status,
            },
            status=http_status,
        )


class AuditLogListAPIView(APIView):
    """List and filter immutable audit logs for compliance oversight."""

    permission_classes = [role_required(RoleCatalog.AUDITOR)]
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        summary="List Audit Logs",
        description="Query append-only audit trail records with filtering by action, resource type, user, and date range.",
        responses={200: AuditLogSerializer(many=True)},
    )
    def get(self, request):
        search = request.query_params.get("search")
        action = request.query_params.get("action")
        resource_type = request.query_params.get("resource_type")
        user_id = request.query_params.get("user_id")
        correlation_id = request.query_params.get("correlation_id")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        qs = list_audit_logs(
            search=search,
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            correlation_id=correlation_id,
            date_from=date_from,
            date_to=date_to,
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        if page is not None:
            serializer = AuditLogSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AuditLogSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuditLogDetailAPIView(RetrieveAPIView):
    """Retrieve full detail for a single audit log entry."""

    permission_classes = [role_required(RoleCatalog.AUDITOR)]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("user")
    lookup_field = "id"


class AuditSummaryAPIView(APIView):
    """Compliance oversight summary statistics and top actions."""

    permission_classes = [role_required(RoleCatalog.AUDITOR)]

    @extend_schema(
        summary="Audit Summary Metrics",
        description="Aggregate audit statistics including daily counts, top actions, and critical security events.",
        responses={200: AuditSummarySerializer},
    )
    def get(self, request):
        data = get_audit_summary()
        return Response(data, status=status.HTTP_200_OK)


def _sanitize_csv_cell(value) -> str:
    """Sanitize cell value against CSV formula injection attacks."""
    if value is None:
        return ""
    str_val = str(value)
    # Characters that Excel or LibreOffice interpret as formula triggers
    if str_val and str_val[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{str_val}"
    return str_val


class AuditLogExportCSVAPIView(APIView):
    """Export filtered audit logs as a formula-sanitized CSV file."""

    permission_classes = [role_required(RoleCatalog.AUDITOR)]

    @extend_schema(
        summary="Export Audit Trail to CSV",
        description="Generates sanitized CSV export of audit records with formula injection protection.",
    )
    def get(self, request):
        search = request.query_params.get("search")
        action = request.query_params.get("action")
        resource_type = request.query_params.get("resource_type")
        user_id = request.query_params.get("user_id")
        correlation_id = request.query_params.get("correlation_id")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        qs = list_audit_logs(
            search=search,
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            correlation_id=correlation_id,
            date_from=date_from,
            date_to=date_to,
        )[:2000]  # Cap export size for safety

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Timestamp (UTC)",
            "Action",
            "Resource Type",
            "Resource ID",
            "Actor Email",
            "IP Address",
            "Correlation ID",
            "Changes JSON",
        ])

        for log in qs:
            user_email = log.user.email if log.user else "SYSTEM"
            changes_str = json.dumps(log.changes, default=str) if log.changes else "{}"
            writer.writerow([
                _sanitize_csv_cell(log.created_at.isoformat()),
                _sanitize_csv_cell(log.action),
                _sanitize_csv_cell(log.resource_type),
                _sanitize_csv_cell(log.resource_id),
                _sanitize_csv_cell(user_email),
                _sanitize_csv_cell(log.ip_address or ""),
                _sanitize_csv_cell(log.correlation_id or ""),
                _sanitize_csv_cell(changes_str),
            ])

        response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="gqt_hrms_audit_trail.csv"'
        return response
