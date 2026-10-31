from datetime import datetime, timezone
from typing import Optional

UNKNOWN_DATE_SCORE = 30.0


def score_recency(published_at: Optional[datetime], *, now: Optional[datetime] = None) -> float:
    """Deterministic recency scoring per section 10.

    An unknown date gets a fixed conservative score - it must never be treated as recent
    just because we couldn't determine otherwise.
    """
    if published_at is None:
        return UNKNOWN_DATE_SCORE

    now = now or datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    age_days = (now - published_at).days
    if age_days < 0:
        age_days = 0

    if age_days <= 30:
        return 100.0
    if age_days <= 90:
        return 80.0
    if age_days <= 180:
        return 60.0
    if age_days <= 365:
        return 35.0
    return 15.0
