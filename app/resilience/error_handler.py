import re

from app.logging_config import get_logger

logger = get_logger(__name__)

_SECRET_PATTERNS = [
    re.compile(r"(api[_-]?key[\"'=:\s]+)([A-Za-z0-9_\-\.]{8,})", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{8,}"),
    re.compile(r"tvly-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"tai-[A-Za-z0-9_\-]{10,}"),
]


class StageExecutionError(Exception):
    """Raised by a workflow stage to signal a handled failure that should be persisted
    to execution_logs with a safe, non-sensitive message and the stage marked failed."""

    def __init__(self, stage: str, message: str, *, recoverable: bool = False):
        super().__init__(message)
        self.stage = stage
        self.recoverable = recoverable


def redact_secrets(text: str) -> str:
    """Strip anything that looks like an API key/bearer token before it reaches logs or
    API responses. Internal exception messages must never leak credentials to clients."""
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def safe_error_message(exc: Exception, *, default: str = "An internal error occurred") -> str:
    """Produce a client-safe error message: redacted, bounded length, no stack trace."""
    try:
        message = redact_secrets(str(exc))
    except Exception:  # noqa: BLE001
        return default
    if not message:
        return default
    return message[:500]
