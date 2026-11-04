"""Recruitment CRM URL Routing."""
from django.urls import path
from apps.crm.views import (
    CompanyListCreateAPIView,
    CompanyDetailAPIView,
    CompanyCheckDuplicateAPIView,
    CompanyHRContactListCreateAPIView,
    HRContactDetailAPIView,
    CompanyOutreachListCreateAPIView,
    FollowUpListCreateAPIView,
    FollowUpDetailAPIView,
    FollowUpCompleteAPIView,
    FollowUpCancelAPIView,
)

app_name = "crm"

urlpatterns = [
    # Company Pipeline Management
    path("companies/", CompanyListCreateAPIView.as_view(), name="company-list-create"),
    path("companies/check-duplicate/", CompanyCheckDuplicateAPIView.as_view(), name="company-check-duplicate"),
    path("companies/<uuid:company_id>/", CompanyDetailAPIView.as_view(), name="company-detail"),

    # HR Contact Directory
    path("companies/<uuid:company_id>/contacts/", CompanyHRContactListCreateAPIView.as_view(), name="company-contacts"),
    path("contacts/<uuid:contact_id>/", HRContactDetailAPIView.as_view(), name="contact-detail"),

    # Outreach Touchpoint Logging
    path("companies/<uuid:company_id>/outreach/", CompanyOutreachListCreateAPIView.as_view(), name="company-outreach"),

    # Follow-Up Task Management
    path("follow-ups/", FollowUpListCreateAPIView.as_view(), name="followup-list-create"),
    path("follow-ups/<uuid:follow_up_id>/", FollowUpDetailAPIView.as_view(), name="followup-detail"),
    path("follow-ups/<uuid:follow_up_id>/complete/", FollowUpCompleteAPIView.as_view(), name="followup-complete"),
    path("follow-ups/<uuid:follow_up_id>/cancel/", FollowUpCancelAPIView.as_view(), name="followup-cancel"),
]

