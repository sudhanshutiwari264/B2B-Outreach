from unittest.mock import AsyncMock, patch

from app.integrations.schemas import NormalizedExtractResult
from app.research.content_extractor import extract_content_for_urls
from app.research.url_crawler import FetchResult
from tests.fakes import FakeTavilyClient


async def test_linkedin_urls_are_restricted_without_any_fetch_attempt():
    tavily = FakeTavilyClient(search_results=[], extracted_contents=[])
    with patch("app.research.content_extractor.fetch_url", new=AsyncMock()) as mock_fetch:
        results = await extract_content_for_urls(
            tavily, ["https://www.linkedin.com/in/jane-doe"]
        )
    mock_fetch.assert_not_called()
    assert results[0].restricted is True
    assert results[0].success is False


async def test_tavily_extract_success_short_circuits_local_fallback():
    class _Tavily(FakeTavilyClient):
        async def extract_urls(self, urls):
            return [
                NormalizedExtractResult(
                    url=urls[0], success=True, raw_content="Full article text here, plenty of content.",
                    title="Article",
                )
            ]

    tavily = _Tavily(search_results=[], extracted_contents=[])
    with patch("app.research.content_extractor.fetch_url", new=AsyncMock()) as mock_fetch:
        results = await extract_content_for_urls(tavily, ["https://news.example.com/a"])
    mock_fetch.assert_not_called()
    assert results[0].success is True
    assert results[0].extraction_method == "tavily_extract"


async def test_tavily_extract_failure_falls_back_to_local_fetch():
    """EC-08: when Tavily Extract fails, the local SSRF-safe fetch + trafilatura fallback
    must be attempted before giving up."""

    class _Tavily(FakeTavilyClient):
        async def extract_urls(self, urls):
            return [NormalizedExtractResult(url=urls[0], success=False, error="403")]

    tavily = _Tavily(search_results=[], extracted_contents=[])
    html = "<html><body><article><p>" + ("Local fallback article body text. " * 10) + "</p></article></body></html>"
    fake_fetch_result = FetchResult(
        url="https://news.example.com/a", final_url="https://news.example.com/a",
        success=True, status_code=200, content_type="text/html",
        raw_bytes=html.encode(), error=None,
    )
    with patch("app.research.content_extractor.fetch_url", new=AsyncMock(return_value=fake_fetch_result)) as mock_fetch:
        results = await extract_content_for_urls(tavily, ["https://news.example.com/a"])
    mock_fetch.assert_called_once()
    assert results[0].success is True
    assert "Local fallback article body text" in results[0].text


async def test_both_extraction_paths_failing_is_recorded_not_fatal():
    class _Tavily(FakeTavilyClient):
        async def extract_urls(self, urls):
            return [NormalizedExtractResult(url=urls[0], success=False, error="timeout")]

    tavily = _Tavily(search_results=[], extracted_contents=[])
    fake_fetch_result = FetchResult(
        url="https://news.example.com/a", final_url=None, success=False,
        status_code=None, content_type=None, raw_bytes=None, error="DNS resolution failed",
    )
    with patch("app.research.content_extractor.fetch_url", new=AsyncMock(return_value=fake_fetch_result)):
        results = await extract_content_for_urls(tavily, ["https://news.example.com/a"])
    assert results[0].success is False
    assert results[0].error is not None
