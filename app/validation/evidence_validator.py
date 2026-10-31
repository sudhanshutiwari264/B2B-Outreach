from typing import Optional, Protocol

from app.models.enums import RelevanceTier


class _SignalLike(Protocol):
    is_disputed: bool
    relevance_tier: Optional[RelevanceTier]
    evidence_excerpt: str
    final_score: Optional[float]


def validate_signal_sufficient_for_outreach(signal: _SignalLike) -> tuple[bool, Optional[str]]:
    """Gate used before strategy/draft generation (section 12-13, EC-12): a signal must
    be undisputed, scored, and at least MEDIUM tier with a real evidence excerpt before
    it can ground an outreach message.
    """
    if signal.is_disputed:
        return False, "Signal is disputed and cannot be used as outreach evidence"
    if signal.final_score is None or signal.relevance_tier is None:
        return False, "Signal has not been scored"
    if signal.relevance_tier == RelevanceTier.LOW:
        return False, "Signal relevance is too low to support a personalized outreach angle"
    if not signal.evidence_excerpt or len(signal.evidence_excerpt.strip()) < 5:
        return False, "Signal has no supporting evidence excerpt"
    return True, None


def select_best_usable_signal(signals: list[_SignalLike]) -> Optional[_SignalLike]:
    """Pick the single strongest signal that passes the sufficiency gate, or None if no
    signal is strong enough - callers must then return insufficient_evidence (EC-12)
    rather than forcing a weak personalization angle."""
    usable = [s for s in signals if validate_signal_sufficient_for_outreach(s)[0]]
    if not usable:
        return None
    return max(usable, key=lambda s: s.final_score or 0)
