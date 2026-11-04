"""Centralized Exception Handling for REST API."""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from apps.core.middleware import get_current_correlation_id

logger = logging.getLogger("apps.core.exceptions")


def custom_exception_handler(exc, context):
    """Intercept DRF exceptions and standardize response schema with correlation ID."""
    response = exception_handler(exc, context)
    correlation_id = get_current_correlation_id()

    if response is not None:
        custom_data = {
            "status_code": response.status_code,
            "correlation_id": correlation_id,
        }
        if isinstance(response.data, dict):
            custom_data.update(response.data)
        else:
            custom_data["detail"] = response.data
        response.data = custom_data
        return response

    # Unhandled server errors (HTTP 500)
    logger.exception("Unhandled server exception caught: %s", str(exc))
    return Response(
        {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error": "InternalServerError",
            "detail": "An internal server error occurred. Please contact system support.",
            "correlation_id": correlation_id,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
