"""Portal views and diagnostic endpoints."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from drf_spectacular.utils import extend_schema

from apps.portal.client import StudentPortalClient
from apps.accounts.permissions import IsAdminOrSuperUser


class PortalStatusAPIView(APIView):
    """Diagnostic endpoint checking Student Portal configuration and availability."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Student Portal Integration Health & Config Status",
        responses={200: dict},
    )
    def get(self, request):
        client = StudentPortalClient()
        status_info = {
            "enabled": client.enabled,
            "configured": client.is_configured(),
            "base_url": client.base_url if client.enabled else None,
        }

        if client.enabled:
            try:
                ping_res = client.ping()
                status_info["connectivity"] = "connected"
                status_info["remote_response"] = ping_res
            except Exception as exc:
                status_info["connectivity"] = "unreachable"
                status_info["error"] = str(exc)
        else:
            status_info["connectivity"] = "disabled_offline_mode"

        return Response(status_info)
