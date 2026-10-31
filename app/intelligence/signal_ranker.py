from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.intelligence.evidence_scorer import score_evidence_quality
from app.intelligence.recency_scorer import score_recency
from app.intelligence.relevance_scorer import score_business_impact, score_relevance
from app.models.enums import EvidenceType, RelevanceTier, SignalType

RELEVANCE_WEIGHT = 0.40
BUSINESS_IMPACT_WEIGHT = 0.30
RECENCY_WEIGHT = 0.20
EVIDENCE_QUALITY_WEIGHT = 0.10

HIGH_TIER_THRESHOLD = 80
MEDIUM_TIER_THRESHOLD = 60


@dataclass
class SignalScoreBreakdown:
    relevance_score: float
    business_impact_score: float
    recency_score: float
    evidence_quality_score: float
    final_score: float
    relevance_tier: RelevanceTier


def classify_tier(final_score: float) -> RelevanceTier:
    if final_score >= HIGH_TIER_THRESHOLD:
        return RelevanceTier.HIGH
    if final_score >= MEDIUM_TIER_THRESHOLD:
        return RelevanceTier.MEDIUM
    return RelevanceTier.LOW


def score_signal(
    *,
    signal_type: SignalType,
    entity_matches_prospect: bool,
    company_matches: bool,
    description: str,
    product_context: Optional[str],
    published_at: Optional[datetime],
    evidence_type: EvidenceType,
    domain: Optional[str],
    excerpt_is_grounded: bool,
    corroborating_source_count: int = 0,
) -> SignalScoreBreakdown:
    """Deterministic, explainable scoring per section 10's weighted formula. The LLM never
    sets final_score directly - it only supplies the raw signal; every component here is
    plain Python arithmetic over verifiable inputs."""
    relevance = score_relevance(
        signal_type,
        entity_matches_prospect=entity_matches_prospect,
        company_matches=company_matches,
        description=description,
        product_context=product_context,
    )
    business_impact = score_business_impact(signal_type)
    recency = score_recency(published_at)
    evidence_quality = score_evidence_quality(
        evidence_type,
        domain=domain,
        excerpt_is_grounded=excerpt_is_grounded,
        corroborating_source_count=corroborating_source_count,
    )

    final_score = (
        relevance * RELEVANCE_WEIGHT
        + business_impact * BUSINESS_IMPACT_WEIGHT
        + recency * RECENCY_WEIGHT
        + evidence_quality * EVIDENCE_QUALITY_WEIGHT
    )

    return SignalScoreBreakdown(
        relevance_score=relevance,
        business_impact_score=business_impact,
        recency_score=recency,
        evidence_quality_score=evidence_quality,
        final_score=round(final_score, 2),
        relevance_tier=classify_tier(final_score),
    )


@dataclass
class RankableSignal:
    id: str
    final_score: float
    is_disputed: bool


def select_top_signals(
    signals: list[RankableSignal],
    *,
    min_score: float = MEDIUM_TIER_THRESHOLD,
    top_n: int = 5,
    exclude_disputed: bool = True,
) -> list[RankableSignal]:
    """Signal-selection stage: rank by final_score, excluding disputed signals (section 11:
    disputed facts must never enter outreach) and anything below the minimum tier."""
    candidates = [s for s in signals if s.final_score >= min_score]
    if exclude_disputed:
        candidates = [s for s in candidates if not s.is_disputed]
    candidates.sort(key=lambda s: s.final_score, reverse=True)
    return candidates[:top_n]
