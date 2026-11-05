"""URL patterns for Candidate Submissions & Profile Dispatch (MOD-007)."""
from django.urls import path
from apps.submissions.views import (
    SubmissionPackageListCreateAPIView,
    SubmissionPackageDetailAPIView,
    SubmissionPackageAddCandidateAPIView,
    SubmissionPackageApproveAPIView,
    SubmissionPackageDispatchAPIView,
    SubmissionPackageAcknowledgeAPIView,
    SubmissionPackageRosterCSVAPIView,
)

app_name = "submissions"

urlpatterns = [
    path("", SubmissionPackageListCreateAPIView.as_view(), name="submission_list_create"),
    path("<uuid:id>/", SubmissionPackageDetailAPIView.as_view(), name="submission_detail"),
    path("<uuid:id>/add-candidate/", SubmissionPackageAddCandidateAPIView.as_view(), name="submission_add_candidate"),
    path("<uuid:id>/approve/", SubmissionPackageApproveAPIView.as_view(), name="submission_approve"),
    path("<uuid:id>/dispatch/", SubmissionPackageDispatchAPIView.as_view(), name="submission_dispatch"),
    path("<uuid:id>/acknowledge/", SubmissionPackageAcknowledgeAPIView.as_view(), name="submission_acknowledge"),
    path("<uuid:id>/roster-csv/", SubmissionPackageRosterCSVAPIView.as_view(), name="submission_roster_csv"),
]

