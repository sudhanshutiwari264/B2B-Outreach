from datetime import datetime, timedelta, timezone

from app.intelligence.evidence_scorer import score_evidence_quality
from app.intelligence.recency_scorer import UNKNOWN_DATE_SCORE, score_recency
from app.intelligence.relevance_scorer import score_business_impact, score_relevance
from app.intelligence.signal_ranker import RankableSignal, classify_tier, score_signal, select_top_signals
from app.models.enums import EvidenceType, RelevanceTier, SignalType

NOW = datetime(2026, 10, 31, tzinfo=timezone.utc)


def test_recency_scorer_bucket_boundaries():
    assert score_recency(NOW - timedelta(days=10), now=NOW) == 100.0
    assert score_recency(NOW - timedelta(days=60), now=NOW) == 80.0
    assert score_recency(NOW - timedelta(days=150), now=NOW) == 60.0
    assert score_recency(NOW - timedelta(days=300), now=NOW) == 35.0
    assert score_recency(NOW - timedelta(days=800), now=NOW) == 15.0


def test_recency_scorer_unknown_date_is_conservative_not_recent():
    assert score_recency(None) == UNKNOWN_DATE_SCORE
    assert UNKNOWN_DATE_SCORE < 100.0


def test_relevance_scorer_penalizes_entity_and_company_mismatch():
    matched = score_relevance(
        SignalType.FUNDING, entity_matches_prospect=True, company_matches=True, description=""
    )
    mismatched = score_relevance(
        SignalType.FUNDING, entity_matches_prospect=False, company_matches=False, description=""
    )
    assert matched > mismatched


def test_relevance_scorer_product_context_bonus():
    base = score_relevance(
        SignalType.HIRING, entity_matches_prospect=True, company_matches=True,
        description="Company is hiring engineers for workflow automation projects",
        product_context=None,
    )
    boosted = score_relevance(
        SignalType.HIRING, entity_matches_prospect=True, company_matches=True,
        description="Company is hiring engineers for workflow automation projects",
        product_context="workflow automation platform for engineers",
    )
    assert boosted >= base


def test_business_impact_scorer_funding_highest():
    assert score_business_impact(SignalType.FUNDING) >= score_business_impact(SignalType.PUBLIC_SPEAKING)


def test_evidence_scorer_full_page_beats_search_snippet():
    full_page = score_evidence_quality(
        EvidenceType.FULL_PAGE, domain="techcrunch.com", excerpt_is_grounded=True
    )
    snippet = score_evidence_quality(
        EvidenceType.SEARCH_SNIPPET, domain="techcrunch.com", excerpt_is_grounded=True
    )
    assert full_page > snippet


def test_evidence_scorer_ungrounded_excerpt_penalized():
    grounded = score_evidence_quality(EvidenceType.FULL_PAGE, domain="example.com", excerpt_is_grounded=True)
    ungrounded = score_evidence_quality(EvidenceType.FULL_PAGE, domain="example.com", excerpt_is_grounded=False)
    assert grounded > ungrounded


def test_classify_tier_thresholds():
    assert classify_tier(85) == RelevanceTier.HIGH
    assert classify_tier(65) == RelevanceTier.MEDIUM
    assert classify_tier(40) == RelevanceTier.LOW


def test_score_signal_combines_components_with_documented_weights():
    breakdown = score_signal(
        signal_type=SignalType.FUNDING,
        entity_matches_prospect=True,
        company_matches=True,
        description="raised a large funding round",
        product_context=None,
        published_at=NOW - timedelta(days=5),
        evidence_type=EvidenceType.FULL_PAGE,
        domain="techcrunch.com",
        excerpt_is_grounded=True,
    )
    expected = (
        breakdown.relevance_score * 0.40
        + breakdown.business_impact_score * 0.30
        + breakdown.recency_score * 0.20
        + breakdown.evidence_quality_score * 0.10
    )
    assert round(expected, 2) == breakdown.final_score


def test_select_top_signals_excludes_disputed_and_low_scores():
    signals = [
        RankableSignal(id="a", final_score=95, is_disputed=False),
        RankableSignal(id="b", final_score=90, is_disputed=True),
        RankableSignal(id="c", final_score=40, is_disputed=False),
        RankableSignal(id="d", final_score=70, is_disputed=False),
    ]
    top = select_top_signals(signals, top_n=5)
    ids = [s.id for s in top]
    assert ids == ["a", "d"]
