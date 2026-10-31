from dataclasses import dataclass, field
from urllib.parse import urlparse

from app.integrations.schemas import NormalizedSearchResult
from app.logging_config import get_logger
from app.models.enums import EvidenceType, ExtractionStatus, SourceType, VerificationStatus
from app.research.schemas import ExtractedContent
from app.research.url_safety import normalize_url

logger = get_logger(__name__)

_CATEGORY_TO_SOURCE_TYPE = {
    "linkedin_profile": SourceType.LINKEDIN_PROFILE,
    "linkedin_post": SourceType.LINKEDIN_POST,
    "job_change": SourceType.LINKEDIN_PROFILE,
    "company_news": SourceType.COMPANY_NEWS,
    "funding": SourceType.FUNDING_NEWS,
    "hiring": SourceType.JOB_POSTING,
    "partnership": SourceType.COMPANY_NEWS,
    "company_growth": SourceType.COMPANY_NEWS,
    "business_challenge": SourceType.COMPANY_NEWS,
    "industry_development": SourceType.INDUSTRY_PUBLICATION,
    "interview": SourceType.INTERVIEW,
    "podcast": SourceType.PODCAST,
    "public_speaking": SourceType.INDUSTRY_PUBLICATION,
    "thought_leadership": SourceType.INDUSTRY_PUBLICATION,
}


@dataclass
class ValidatedSource:
    url: str
    normalized_url: str
    title: str | None
    domain: str | None
    source_type: SourceType
    evidence_type: EvidenceType
    content: str | None
    content_hash: str | None
    published_at: str | None
    extraction_status: ExtractionStatus
    extraction_error: str | None
    verification_status: VerificationStatus
    raw_metadata: dict = field(default_factory=dict)


def _classify_source_type(category_hint: str, url: str) -> SourceType:
    """Classify by URL path for linkedin.com (authoritative - search category hints can be
    imprecise since engines don't always respect path-scoped queries), otherwise by the
    originating query's category hint.
    """
    domain = (urlparse(url).hostname or "").lower()
    if domain == "linkedin.com" or domain.endswith(".linkedin.com"):
        path = urlparse(url).path.lower()
        if "/posts/" in path or "/pulse/" in path:
            return SourceType.LINKEDIN_POST
        if "/in/" in path:
            return SourceType.LINKEDIN_PROFILE
        return SourceType.LINKEDIN_PROFILE
    return _CATEGORY_TO_SOURCE_TYPE.get(category_hint, SourceType.OTHER)


def deduplicate_search_results(
    results: list[NormalizedSearchResult],
) -> list[NormalizedSearchResult]:
    """EC-07: normalize + deduplicate URLs before any extraction is attempted."""
    seen: dict[str, NormalizedSearchResult] = {}
    for r in results:
        key = normalize_url(r.url)
        if key not in seen:
            seen[key] = r
    return list(seen.values())


def build_validated_sources(
    search_results: list[NormalizedSearchResult],
    extracted: list[ExtractedContent],
) -> list[ValidatedSource]:
    """Merge search-snippet evidence with (optional) full-page extraction into unified
    source records, deduplicating identical content by hash (EC-07).

    Evidence types are never conflated: a source only gets EvidenceType.FULL_PAGE if a
    real extraction succeeded. Everything else stays SEARCH_SNIPPET or RESTRICTED so
    downstream scoring/signal-extraction can weight it correctly.
    """
    extracted_by_url = {e.url: e for e in extracted}
    seen_hashes: set[str] = set()
    validated: list[ValidatedSource] = []

    for result in search_results:
        extraction = extracted_by_url.get(result.url)
        domain = (urlparse(result.url).hostname or "").lower() or None
        source_type = _classify_source_type(result.category_hint, result.url)

        if extraction and extraction.restricted:
            validated.append(
                ValidatedSource(
                    url=result.url,
                    normalized_url=normalize_url(result.url),
                    title=result.title,
                    domain=domain,
                    source_type=source_type,
                    evidence_type=EvidenceType.SEARCH_SNIPPET,
                    content=result.snippet,
                    content_hash=None,
                    published_at=result.published_date,
                    extraction_status=ExtractionStatus.RESTRICTED,
                    extraction_error=extraction.error,
                    verification_status=VerificationStatus.RESTRICTED,
                    raw_metadata={"query": result.query, "category_hint": result.category_hint},
                )
            )
            continue

        if extraction and extraction.success and extraction.text:
            content_hash = extraction.content_hash
            if content_hash and content_hash in seen_hashes:
                logger.info("source_validator.duplicate_content_skipped", url=result.url)
                continue
            if content_hash:
                seen_hashes.add(content_hash)
            validated.append(
                ValidatedSource(
                    url=result.url,
                    normalized_url=normalize_url(result.url),
                    title=extraction.title or result.title,
                    domain=domain,
                    source_type=source_type,
                    evidence_type=EvidenceType.FULL_PAGE,
                    content=extraction.text,
                    content_hash=content_hash,
                    published_at=extraction.published_at or result.published_date,
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_error=None,
                    verification_status=VerificationStatus.PENDING,
                    raw_metadata={
                        "query": result.query,
                        "category_hint": result.category_hint,
                        "extraction_method": extraction.extraction_method,
                    },
                )
            )
            continue

        # Extraction failed or was never attempted: fall back to search-snippet evidence.
        validated.append(
            ValidatedSource(
                url=result.url,
                normalized_url=normalize_url(result.url),
                title=result.title,
                domain=domain,
                source_type=source_type,
                evidence_type=EvidenceType.SEARCH_SNIPPET,
                content=result.snippet,
                content_hash=None,
                published_at=result.published_date,
                extraction_status=ExtractionStatus.FAILED if extraction else ExtractionStatus.SKIPPED,
                extraction_error=extraction.error if extraction else None,
                verification_status=VerificationStatus.PENDING,
                raw_metadata={"query": result.query, "category_hint": result.category_hint},
            )
        )

    return validated
