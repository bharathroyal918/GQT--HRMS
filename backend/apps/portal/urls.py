"""Portal URL routing."""
from django.urls import path
from apps.portal.views import PortalStatusAPIView

app_name = "portal"

urlpatterns = [
    path("status/", PortalStatusAPIView.as_view(), name="status"),
]
