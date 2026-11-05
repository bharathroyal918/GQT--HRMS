"""URL patterns for Student Preparation and Readiness Gate (MOD-006)."""
from django.urls import path
from apps.preparation.views import (
    ResumeReviewListCreateAPIView,
    AssessmentRecordListCreateAPIView,
    MockInterviewListCreateAPIView,
    ReadinessStatusAPIView,
    CertifyReadinessAPIView,
)

app_name = "preparation"

urlpatterns = [
    path("reviews/", ResumeReviewListCreateAPIView.as_view(), name="resume_reviews"),
    path("assessments/", AssessmentRecordListCreateAPIView.as_view(), name="assessments"),
    path("mocks/", MockInterviewListCreateAPIView.as_view(), name="mock_interviews"),
    path("readiness/status/", ReadinessStatusAPIView.as_view(), name="readiness_status"),
    path("readiness/certify/", CertifyReadinessAPIView.as_view(), name="certify_readiness"),
]

