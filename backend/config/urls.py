"""Root URL Configuration for GQT HRMS & Recruitment CRM Platform.

Versioned API Namespace: /api/v1/
OpenAPI 3.1 Documentation: /api/v1/schema/swagger/ and /api/v1/schema/redoc/
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Versioned API Namespace: /api/v1/
    path(
        "api/v1/",
        include(
            [
                # Core Infrastructure & Diagnostics
                path("", include("apps.core.urls", namespace="core")),

                # Identity, Authentication & Role Management
                path("auth/", include("apps.accounts.urls", namespace="accounts")),

                # Student Portal Integration Gateway
                path("portal/", include("apps.portal.urls", namespace="portal")),

                # Recruitment CRM: Company Acquisition, HR Contacts & Outreach
                path("crm/", include("apps.crm.urls", namespace="crm")),

                # Job Requirements: JDs, 5-Point Verification & Segregation of Duties Approvals
                path("jobs/", include("apps.jobs.urls", namespace="jobs")),

                # Creative Studio: Requisitions, Versioning, Compliance & SoD Sign-Off
                path("creatives/", include("apps.creatives.urls", namespace="creatives")),

                # Student Placement Operations & Eligibility Engine (MOD-005)
                path("students/", include("apps.students.urls", namespace="students")),

                # Student Preparation, Assessments & Step 23 Gate (MOD-006)
                path("preparation/", include("apps.preparation.urls", namespace="preparation")),

                # Candidate Submissions & Profile Dispatch (MOD-007)
                path("submissions/", include("apps.submissions.urls", namespace="submissions")),

                # Placement Drives & Multi-Round Interviews (MOD-008)
                path("interviews/", include("apps.interviews.urls", namespace="interviews")),

                # Placement Management, Offers & Joining Verification (MOD-009)
                path("placements/", include("apps.placements.urls", namespace="placements")),

                # OpenAPI 3.1 Documentation
                path("schema/", SpectacularAPIView.as_view(), name="schema"),
                path(
                    "schema/swagger/",
                    SpectacularSwaggerView.as_view(url_name="schema"),
                    name="swagger-ui",
                ),
                path(
                    "schema/redoc/",
                    SpectacularRedocView.as_view(url_name="schema"),
                    name="redoc",
                ),
            ]
        ),
    ),
]
