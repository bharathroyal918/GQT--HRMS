"""URL Routing for Job Requirements, Verification, and Approval Workflow."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.jobs.views import (
    JobRequirementViewSet,
    JobVerificationQueueView,
    JobApprovalQueueView,
    JobWorkflowMetricsView,
)

app_name = "jobs"

router = DefaultRouter()
router.register(r"requirements", JobRequirementViewSet, basename="requirement")

urlpatterns = [
    path("verification-queue/", JobVerificationQueueView.as_view(), name="verification-queue"),
    path("approval-queue/", JobApprovalQueueView.as_view(), name="approval-queue"),
    path("metrics/", JobWorkflowMetricsView.as_view(), name="metrics"),
    path("", include(router.urls)),
]

