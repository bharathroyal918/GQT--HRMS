"""Structured Logging and Sensitive Data Redaction Filter."""
import logging
import re
from apps.core.middleware import get_current_correlation_id

SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|secret|token|api_key|access_token|refresh_token|authorization)",
    re.IGNORECASE,
)


class SensitiveDataFilter(logging.Filter):
    """Logging filter that injects correlation ID and redacts sensitive parameters."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_current_correlation_id()

        # Sanitize message string if present
        if isinstance(record.msg, str):
            record.msg = re.sub(
                r'(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*',
                r'\1[REDACTED_TOKEN]',
                record.msg,
            )
            record.msg = re.sub(
                r'((?:password|secret|token|api_key)\s*[:=]\s*)[^\s,;&]+',
                r'\1[REDACTED]',
                record.msg,
                flags=re.IGNORECASE,
            )
        return True
