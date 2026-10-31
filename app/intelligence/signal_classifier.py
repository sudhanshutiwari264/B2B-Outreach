from datetime import datetime, timezone
from typing import Optional

from dateutil import parser as dateutil_parser

from app.logging_config import get_logger

logger = get_logger(__name__)


def parse_published_at(raw: Optional[str]) -> Optional[datetime]:
    """Safely parse an LLM/source-provided date string into a UTC datetime.

    Unknown or unparseable dates return None rather than guessing - recency_scorer treats
    None as "unknown" and never silently assumes recency (section 10)."""
    if not raw or not raw.strip():
        return None
    try:
        parsed = dateutil_parser.parse(raw, fuzzy=True)
    except (ValueError, OverflowError):
        logger.info("signal_classifier.unparseable_date", raw=raw)
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    if parsed > now or parsed.year < 2000:
        logger.info("signal_classifier.implausible_date_discarded", raw=raw, parsed=str(parsed))
        return None

    return parsed


def entity_matches_prospect(signal_entity: str, prospect_name: str) -> bool:
    """Loose check that the LLM-reported entity is plausibly the prospect we researched,
    guarding against name-collision cross-contamination (EC-11)."""
    a = {w.lower() for w in signal_entity.split() if len(w) > 1}
    b = {w.lower() for w in prospect_name.split() if len(w) > 1}
    if not a or not b:
        return True
    return bool(a & b)
