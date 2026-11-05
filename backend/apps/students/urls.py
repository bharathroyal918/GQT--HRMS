"""URL patterns for Student Operations and Eligibility Engine (MOD-005)."""
from django.urls import path
from apps.students.views import (
    StudentListCreateAPIView,
    StudentDetailAPIView,
    StudentMetricsAPIView,
    EligibilityCheckAPIView,
    EligibilityOverrideAPIView,
    DriveRegistrationListCreateAPIView,
    CandidateCohortFinalizeAPIView,
)

app_name = "students"

urlpatterns = [
    path("", StudentListCreateAPIView.as_view(), name="student_list_create"),
    path("metrics/", StudentMetricsAPIView.as_view(), name="student_metrics"),
    path("eligibility/check/", EligibilityCheckAPIView.as_view(), name="eligibility_check"),
    path("eligibility/override/", EligibilityOverrideAPIView.as_view(), name="eligibility_override"),
    path("registrations/", DriveRegistrationListCreateAPIView.as_view(), name="drive_registrations"),
    path("cohorts/<uuid:job_id>/finalize/", CandidateCohortFinalizeAPIView.as_view(), name="cohort_finalize"),
    path("<uuid:id>/", StudentDetailAPIView.as_view(), name="student_detail"),
]

