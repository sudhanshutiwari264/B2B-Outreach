from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.integrations.tavily_client import TavilyClient, TavilyIntegrationError, TavilyNotConfiguredError


def _client_with_fake_sdk() -> TavilyClient:
    settings = Settings(tavily_api_key="fake-key-for-tests")
    client = TavilyClient(settings)
    client._sdk = MagicMock()
    return client


async def test_search_web_normalizes_results():
    client = _client_with_fake_sdk()
    client._sdk.search.return_value = {
        "results": [
            {"url": "https://example.com/a", "title": "A", "content": "snippet a", "score": 0.9, "published_date": "2026-01-01"},
            {"url": "https://example.com/b", "title": "B", "content": "snippet b", "score": 0.5},
        ]
    }
    results = await client.search_web("test query", category_hint="company_news")
    assert len(results) == 2
    assert results[0].url == "https://example.com/a"
    assert results[0].category_hint == "company_news"
    assert results[0].query == "test query"


async def test_search_web_skips_results_without_url():
    client = _client_with_fake_sdk()
    client._sdk.search.return_value = {"results": [{"title": "No URL", "content": "x"}]}
    results = await client.search_web("test query")
    assert results == []


async def test_extract_urls_handles_mixed_success_and_failure():
    client = _client_with_fake_sdk()
    client._sdk.extract.return_value = {
        "results": [{"url": "https://example.com/good", "raw_content": "full text", "title": "Good"}],
        "failed_results": [{"url": "https://example.com/bad", "error": "403 forbidden"}],
    }
    results = await client.extract_urls(["https://example.com/good", "https://example.com/bad"])
    by_url = {r.url: r for r in results}
    assert by_url["https://example.com/good"].success is True
    assert by_url["https://example.com/bad"].success is False


async def test_extract_urls_empty_list_short_circuits():
    client = _client_with_fake_sdk()
    results = await client.extract_urls([])
    assert results == []
    client._sdk.extract.assert_not_called()


async def test_not_configured_raises_clear_error():
    settings = Settings(tavily_api_key=None)
    client = TavilyClient(settings)
    assert client.is_configured is False
    with pytest.raises(TavilyNotConfiguredError):
        await client.search_web("anything")


async def test_search_web_wraps_persistent_sdk_errors():
    client = _client_with_fake_sdk()
    client._sdk.search.side_effect = RuntimeError("network down")
    with pytest.raises(TavilyIntegrationError):
        await client.search_web("test query", max_results=1)
