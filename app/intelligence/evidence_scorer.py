from typing import Optional

from app.models.enums import EvidenceType

_CONTENT_AVAILABILITY_SCORE = {
    EvidenceType.FULL_PAGE: 50,
    EvidenceType.USER_PROVIDED: 40,
    EvidenceType.SEARCH_SNIPPET: 28,
    EvidenceType.METADATA: 20,
}

_REPUTABLE_DOMAINS = {
    "reuters.com", "bloomberg.com", "techcrunch.com", "forbes.com", "wsj.com",
    "businesswire.com", "prnewswire.com", "cnbc.com", "ft.com", "theverge.com",
    "wired.com", "nytimes.com", "fortune.com", "crunchbase.com", "sec.gov",
}


def score_evidence_quality(
    evidence_type: EvidenceType,
    *,
    domain: Optional[str],
    excerpt_is_grounded: bool,
    corroborating_source_count: int = 0,
) -> float:
    """Deterministic evidence-quality scoring per section 10:
    - whether full source content was available
    - whether the source is attributable (has a real domain)
    - whether the claim is directly supported (verbatim-grounded excerpt)
    - whether the source is a generally reliable outlet
    - whether independent corroboration exists
    """
    score = _CONTENT_AVAILABILITY_SCORE.get(evidence_type, 10)

    if domain:
        score += 15
        normalized = domain.lower().lstrip("www.")
        if any(normalized == d or normalized.endswith("." + d) for d in _REPUTABLE_DOMAINS):
            score += 15
        else:
            score += 5
    else:
        score += 0

    if excerpt_is_grounded:
        score += 20
    else:
        score -= 20

    if corroborating_source_count >= 1:
        score += min(10, corroborating_source_count * 5)

    return max(0.0, min(100.0, float(score)))
