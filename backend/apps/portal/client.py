"""Client gateway for communicating with the GQT Student Portal.

Designed with circuit-breaker awareness, mock fallback during foundation/dev,
custom timeouts, correlation ID propagation, and retry backoff.
"""
import json
import logging
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

from django.conf import settings
from apps.core.middleware import get_current_correlation_id
from apps.portal.exceptions import (
    PortalAPIError,
    PortalAuthError,
    PortalConnectionError,
    PortalDisabledError,
    PortalTimeoutError,
)

logger = logging.getLogger("django.request")


class StudentPortalClient:
    """Gateway client for the external GQT Student Portal REST API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        hr_email: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout_seconds: float = 5.0,
        max_retries: int = 2,
    ):
        self.base_url = (base_url or getattr(settings, "STUDENT_PORTAL_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or getattr(settings, "STUDENT_PORTAL_API_KEY", "")
        self.hr_email = hr_email or getattr(settings, "STUDENT_PORTAL_HR_EMAIL", "")
        self.enabled = (
            enabled if enabled is not None else getattr(settings, "STUDENT_PORTAL_ENABLED", False)
        )
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def is_configured(self) -> bool:
        """Checks whether the portal integration is enabled and configured."""
        return bool(self.enabled and self.base_url and self.api_key)

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "GQT-HRMS-Gateway/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.hr_email:
            headers["X-Service-Email"] = self.hr_email

        corr_id = get_current_correlation_id()
        if corr_id:
            headers["X-Correlation-ID"] = corr_id

        return headers

    def _execute_request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes an HTTP request to the Student Portal with timeout and retry handling."""
        if not self.enabled:
            raise PortalDisabledError("Student Portal integration is currently disabled in settings.")

        url = f"{self.base_url}/{path.lstrip('/')}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = self._build_headers()

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 2):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                    raw_body = response.read().decode("utf-8")
                    if raw_body:
                        try:
                            return json.loads(raw_body)
                        except json.JSONDecodeError:
                            return {"raw": raw_body}
                    return {"status": "ok"}
            except urllib.error.HTTPError as http_err:
                body = http_err.read().decode("utf-8", errors="replace")
                if http_err.code in (401, 403):
                    raise PortalAuthError(f"Authentication failed: HTTP {http_err.code}") from http_err
                if http_err.code >= 500 and attempt <= self.max_retries:
                    time.sleep(0.2 * attempt)
                    last_error = http_err
                    continue
                raise PortalAPIError(status_code=http_err.code, detail=body) from http_err
            except urllib.error.URLError as url_err:
                if "timed out" in str(url_err.reason).lower():
                    last_error = PortalTimeoutError(f"Request timed out after {self.timeout_seconds}s")
                else:
                    last_error = PortalConnectionError(f"Connection failed: {url_err.reason}")

                if attempt <= self.max_retries:
                    time.sleep(0.2 * attempt)
                    continue
                raise last_error from url_err
            except TimeoutError as te:
                last_error = PortalTimeoutError(f"Request timed out: {te}")
                if attempt <= self.max_retries:
                    time.sleep(0.2 * attempt)
                    continue
                raise last_error from te

        raise PortalConnectionError("Max retries exceeded without successful response")

    def ping(self) -> Dict[str, Any]:
        """Health check probe to external portal."""
        if not self.enabled:
            return {"status": "mock", "enabled": False, "message": "Portal integration disabled (local/test mode)"}
        return self._execute_request("GET", "health/")

    def fetch_student(self, usn: str) -> Dict[str, Any]:
        """Fetches student profile and academic metrics from Student Portal by USN."""
        if not self.enabled:
            # Safe mock fallback for development / offline testing
            return {
                "usn": usn,
                "name": f"Mock Student ({usn})",
                "email": f"{usn.lower()}@student.gqt.local",
                "branch": "Computer Science & Engineering",
                "cgpa": 8.45,
                "mock": True,
            }
        return self._execute_request("GET", f"students/{usn}/")
