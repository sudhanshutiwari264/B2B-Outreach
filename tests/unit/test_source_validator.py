from app.integrations.schemas import NormalizedSearchResult
from app.models.enums import EvidenceType, ExtractionStatus, SourceType, VerificationStatus
from app.research.schemas import ExtractedContent
from app.research.source_validator import build_validated_sources, deduplicate_search_results


def test_deduplicate_search_results_collapses_equivalent_urls():
    """EC-07: identical URLs with different tracking params / casing collapse to one."""
    results = [
        NormalizedSearchResult(url="https://example.com/a?utm_source=x", title="A", snippet="s1", query="q", category_hint="other"),
        NormalizedSearchResult(url="https://EXAMPLE.com/a", title="A dup", snippet="s2", query="q", category_hint="other"),
        NormalizedSearchResult(url="https://example.com/b", title="B", snippet="s3", query="q", category_hint="other"),
    ]
    deduped = deduplicate_search_results(results)
    assert len(deduped) == 2


def test_build_validated_sources_dedupes_identical_content_hash():
    """EC-07: two different URLs with identical extracted content should only yield one
    FULL_PAGE source - the duplicate is dropped, not double counted."""
    results = [
        NormalizedSearchResult(url="https://site-a.example.com/story", title="Story", snippet="snippet a", query="q", category_hint="company_news"),
        NormalizedSearchResult(url="https://mirror-b.example.com/story", title="Story mirror", snippet="snippet b", query="q", category_hint="company_news"),
    ]
    extracted = [
        ExtractedContent(url="https://site-a.example.com/story", success=True, text="Identical article body here.", content_hash="hash123", extraction_method="trafilatura"),
        ExtractedContent(url="https://mirror-b.example.com/story", success=True, text="Identical article body here.", content_hash="hash123", extraction_method="trafilatura"),
    ]
    validated = build_validated_sources(results, extracted)
    full_page_sources = [v for v in validated if v.evidence_type == EvidenceType.FULL_PAGE]
    assert len(full_page_sources) == 1


def test_build_validated_sources_marks_linkedin_as_restricted():
    """EC-05: LinkedIn URLs that were never crawled stay as restricted search-snippet evidence."""
    results = [
        NormalizedSearchResult(url="https://www.linkedin.com/in/jane-doe", title="Jane Doe", snippet="Profile snippet", query="q", category_hint="linkedin_profile"),
    ]
    extracted = [
        ExtractedContent(url="https://www.linkedin.com/in/jane-doe", success=False, restricted=True, error="restricted"),
    ]
    validated = build_validated_sources(results, extracted)
    assert len(validated) == 1
    assert validated[0].source_type == SourceType.LINKEDIN_PROFILE
    assert validated[0].evidence_type == EvidenceType.SEARCH_SNIPPET
    assert validated[0].verification_status == VerificationStatus.RESTRICTED


def test_build_validated_sources_falls_back_to_snippet_on_extraction_failure():
    """EC-08: extraction failure still yields usable (lower-confidence) snippet evidence."""
    results = [
        NormalizedSearchResult(url="https://news.example.com/article", title="Article", snippet="Snippet text", query="q", category_hint="company_news"),
    ]
    extracted = [
        ExtractedContent(url="https://news.example.com/article", success=False, error="timeout"),
    ]
    validated = build_validated_sources(results, extracted)
    assert validated[0].extraction_status == ExtractionStatus.FAILED
    assert validated[0].evidence_type == EvidenceType.SEARCH_SNIPPET
    assert validated[0].content == "Snippet text"


def test_classify_linkedin_post_vs_profile_by_url_path():
    results = [
        NormalizedSearchResult(url="https://www.linkedin.com/posts/jane-doe_activity-123", title="Post", snippet="s", query="q", category_hint="linkedin_profile"),
        NormalizedSearchResult(url="https://www.linkedin.com/in/jane-doe", title="Profile", snippet="s", query="q", category_hint="linkedin_profile"),
    ]
    validated = build_validated_sources(results, [])
    by_url = {v.url: v for v in validated}
    assert by_url["https://www.linkedin.com/posts/jane-doe_activity-123"].source_type == SourceType.LINKEDIN_POST
    assert by_url["https://www.linkedin.com/in/jane-doe"].source_type == SourceType.LINKEDIN_PROFILE
