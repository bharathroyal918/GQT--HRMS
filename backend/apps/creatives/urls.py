"""URL Routing for Creative Studio domain."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.creatives.views import (
    CreativeRequestViewSet,
    CreativeVersionViewSet,
    CreativeTriageQueueView,
    CreativeDesignerQueueView,
    CreativeReviewQueueView,
    CreativeHandoffQueueView,
    CreativeStudioMetricsView,
)

app_name = "creatives"

router = DefaultRouter()
router.register(r"requests", CreativeRequestViewSet, basename="request")
router.register(r"versions", CreativeVersionViewSet, basename="version")

urlpatterns = [
    # Operational Queues
    path("queues/triage/", CreativeTriageQueueView.as_view(), name="queue-triage"),
    path("queues/designer/", CreativeDesignerQueueView.as_view(), name="queue-designer"),
    path("queues/review/", CreativeReviewQueueView.as_view(), name="queue-review"),
    path("queues/handoff/", CreativeHandoffQueueView.as_view(), name="queue-handoff"),

    # Studio Analytics
    path("metrics/", CreativeStudioMetricsView.as_view(), name="studio-metrics"),

    # Router ViewSets
    path("", include(router.urls)),
]

