"""Core URL patterns for health probes and audit compliance logging."""
from django.urls import path
from apps.core.views import (
    HealthCheckAPIView,
    ReadinessAPIView,
    AuditLogListAPIView,
    AuditLogDetailAPIView,
    AuditSummaryAPIView,
    AuditLogExportCSVAPIView,
)

app_name = "core"

urlpatterns = [
    path("health/", HealthCheckAPIView.as_view(), name="health"),
    path("ready/", ReadinessAPIView.as_view(), name="ready"),
    path("audit-logs/", AuditLogListAPIView.as_view(), name="audit_log_list"),
    path("audit-logs/summary/", AuditSummaryAPIView.as_view(), name="audit_summary"),
    path("audit-logs/export/", AuditLogExportCSVAPIView.as_view(), name="audit_log_export"),
    path("audit-logs/<uuid:id>/", AuditLogDetailAPIView.as_view(), name="audit_log_detail"),
]
