from typing import Optional

from app.models.enums import SignalType

# Deterministic base weights (section 10: "the LLM must not decide the final numerical
# score without validation" - these tables are the validation).

_RELEVANCE_BASE: dict[SignalType, float] = {
    SignalType.FUNDING: 90,
    SignalType.LEADERSHIP_ANNOUNCEMENT: 85,
    SignalType.JOB_CHANGE: 80,
    SignalType.PRODUCT_DEVELOPMENT: 80,
    SignalType.COMPANY_GROWTH: 75,
    SignalType.BUSINESS_CHALLENGE: 75,
    SignalType.PARTNERSHIP: 70,
    SignalType.HIRING: 70,
    SignalType.THOUGHT_LEADERSHIP: 60,
    SignalType.PROFESSIONAL_ACTIVITY: 55,
    SignalType.PUBLIC_SPEAKING: 55,
    SignalType.INDUSTRY_DEVELOPMENT: 50,
}

_BUSINESS_IMPACT_BASE: dict[SignalType, float] = {
    SignalType.FUNDING: 95,
    SignalType.BUSINESS_CHALLENGE: 85,
    SignalType.HIRING: 80,
    SignalType.PRODUCT_DEVELOPMENT: 80,
    SignalType.COMPANY_GROWTH: 75,
    SignalType.LEADERSHIP_ANNOUNCEMENT: 70,
    SignalType.PARTNERSHIP: 70,
    SignalType.JOB_CHANGE: 60,
    SignalType.INDUSTRY_DEVELOPMENT: 55,
    SignalType.THOUGHT_LEADERSHIP: 45,
    SignalType.PROFESSIONAL_ACTIVITY: 40,
    SignalType.PUBLIC_SPEAKING: 40,
}

ENTITY_MISMATCH_PENALTY = 25
MAX_PRODUCT_CONTEXT_BONUS = 10


def _product_context_overlap_bonus(description: str, product_context: Optional[str]) -> float:
    if not product_context:
        return 0.0
    desc_words = {w.lower().strip(".,:;") for w in description.split() if len(w) > 3}
    ctx_words = {w.lower().strip(".,:;") for w in product_context.split() if len(w) > 3}
    if not desc_words or not ctx_words:
        return 0.0
    overlap = len(desc_words & ctx_words)
    return min(MAX_PRODUCT_CONTEXT_BONUS, overlap * 2.5)


def score_relevance(
    signal_type: SignalType,
    *,
    entity_matches_prospect: bool,
    company_matches: bool,
    description: str = "",
    product_context: Optional[str] = None,
) -> float:
    score = _RELEVANCE_BASE.get(signal_type, 50)
    if not entity_matches_prospect:
        score -= ENTITY_MISMATCH_PENALTY
    if not company_matches:
        score -= ENTITY_MISMATCH_PENALTY / 2
    score += _product_context_overlap_bonus(description, product_context)
    return max(0.0, min(100.0, score))


def score_business_impact(signal_type: SignalType) -> float:
    return max(0.0, min(100.0, _BUSINESS_IMPACT_BASE.get(signal_type, 45)))
