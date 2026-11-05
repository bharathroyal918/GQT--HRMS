"""URL patterns for Placement Drives & Multi-Round Interviews (MOD-008)."""
from django.urls import path
from apps.interviews.views import (
    PlacementDriveListCreateAPIView,
    PlacementDriveDetailAPIView,
    InterviewRoundCreateAPIView,
    InterviewSlotScheduleAPIView,
    InterviewSlotOutcomeUpdateAPIView,
)

app_name = "interviews"

urlpatterns = [
    path("", PlacementDriveListCreateAPIView.as_view(), name="drive_list_create"),
    path("<uuid:id>/", PlacementDriveDetailAPIView.as_view(), name="drive_detail"),
    path("<uuid:drive_id>/rounds/", InterviewRoundCreateAPIView.as_view(), name="round_create"),
    path("rounds/<uuid:round_id>/schedule/", InterviewSlotScheduleAPIView.as_view(), name="slot_schedule"),
    path("slots/<uuid:slot_id>/outcome/", InterviewSlotOutcomeUpdateAPIView.as_view(), name="slot_outcome"),
]

