"""Core URL patterns for health and readiness probes."""
from django.urls import path
from apps.core.views import HealthCheckAPIView, ReadinessAPIView

app_name = "core"

urlpatterns = [
    path("health/", HealthCheckAPIView.as_view(), name="health"),
    path("ready/", ReadinessAPIView.as_view(), name="ready"),
]
