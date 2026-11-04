"""Core Infrastructure Views: Health, Readiness, and Diagnostics."""
from django.conf import settings
from django.db import connection
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers


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
