import asyncio
from typing import Any, Optional

from tavily import TavilyClient as _TavilySDKClient

from app.config import Settings, get_settings
from app.integrations.schemas import NormalizedExtractResult, NormalizedSearchResult
from app.logging_config import get_logger
from app.resilience.retry_manager import RetryExhaustedError, retry_with_backoff

logger = get_logger(__name__)


class TavilyIntegrationError(Exception):
    """Raised when Tavily cannot be reached or returns an unusable response."""


class TavilyNotConfiguredError(TavilyIntegrationError):
    """Raised when TAVILY_API_KEY is missing."""


class TavilyClient:
    """Thin, resilient wrapper around the official tavily-python SDK.

    The SDK is synchronous (requests-based); every call is pushed to a worker thread via
    asyncio.to_thread so it never blocks the FastAPI event loop. All methods return
    normalized internal schemas, never raw Tavily payloads, so callers never depend on
    Tavily's wire format.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        if not self._settings.tavily_configured:
            self._sdk: Optional[_TavilySDKClient] = None
        else:
            self._sdk = _TavilySDKClient(api_key=self._settings.tavily_api_key)

    @property
    def is_configured(self) -> bool:
        return self._sdk is not None

    def _require_sdk(self) -> _TavilySDKClient:
        if self._sdk is None:
            raise TavilyNotConfiguredError(
                "TAVILY_API_KEY is not set. Add it to your .env to enable web research."
            )
        return self._sdk

    async def _call(self, fn, *, max_attempts: int = 3, timeout: float = 20.0, **kwargs) -> Any:
        sdk = self._require_sdk()

        async def _attempt():
            return await asyncio.wait_for(asyncio.to_thread(fn, sdk, **kwargs), timeout=timeout)

        try:
            return await retry_with_backoff(
                _attempt,
                max_attempts=max_attempts,
                retriable_exceptions=(Exception,),
            )
        except RetryExhaustedError as exc:
            logger.error("tavily.call_failed", error=str(exc.last_error))
            raise TavilyIntegrationError(str(exc.last_error)) from exc

    @staticmethod
    def _do_search(sdk: _TavilySDKClient, **kwargs) -> dict:
        return sdk.search(**kwargs)

    @staticmethod
    def _do_extract(sdk: _TavilySDKClient, **kwargs) -> dict:
        return sdk.extract(**kwargs)

    def _normalize_search_response(
        self, response: dict, query: str, category_hint: str
    ) -> list[NormalizedSearchResult]:
        results = response.get("results") or []
        normalized: list[NormalizedSearchResult] = []
        for item in results:
            url = item.get("url")
            if not url:
                continue
            normalized.append(
                NormalizedSearchResult(
                    url=url,
                    title=item.get("title"),
                    snippet=item.get("content") or "",
                    search_score=item.get("score"),
                    published_date=item.get("published_date"),
                    query=query,
                    category_hint=category_hint,
                )
            )
        return normalized

    async def search_web(
        self,
        query: str,
        *,
        category_hint: str = "other",
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
    ) -> list[NormalizedSearchResult]:
        kwargs: dict[str, Any] = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        }
        if include_domains:
            kwargs["include_domains"] = include_domains
        if exclude_domains:
            kwargs["exclude_domains"] = exclude_domains

        response = await self._call(self._do_search, **kwargs)
        return self._normalize_search_response(response, query, category_hint)

    async def discover_linkedin_profile(
        self, query: str, *, max_results: int = 5
    ) -> list[NormalizedSearchResult]:
        return await self.search_web(
            query,
            category_hint="linkedin_profile",
            max_results=max_results,
            include_domains=["linkedin.com"],
        )

    async def discover_linkedin_posts(
        self, query: str, *, max_results: int = 5
    ) -> list[NormalizedSearchResult]:
        return await self.search_web(
            query,
            category_hint="linkedin_post",
            max_results=max_results,
            include_domains=["linkedin.com"],
        )

    async def search_company_news(
        self, query: str, *, max_results: int = 5
    ) -> list[NormalizedSearchResult]:
        return await self.search_web(query, category_hint="company_news", max_results=max_results)

    async def search_company_hiring(
        self, query: str, *, max_results: int = 5
    ) -> list[NormalizedSearchResult]:
        return await self.search_web(query, category_hint="hiring", max_results=max_results)

    async def search_funding(
        self, query: str, *, max_results: int = 5
    ) -> list[NormalizedSearchResult]:
        return await self.search_web(query, category_hint="funding", max_results=max_results)

    async def extract_urls(self, urls: list[str]) -> list[NormalizedExtractResult]:
        if not urls:
            return []
        try:
            response = await self._call(self._do_extract, urls=urls)
        except TavilyIntegrationError as exc:
            logger.warning("tavily.extract_failed_all", error=str(exc), url_count=len(urls))
            return [
                NormalizedExtractResult(url=u, success=False, error=str(exc)) for u in urls
            ]

        results: list[NormalizedExtractResult] = []
        succeeded_urls = set()
        for item in response.get("results") or []:
            url = item.get("url")
            if not url:
                continue
            succeeded_urls.add(url)
            results.append(
                NormalizedExtractResult(
                    url=url,
                    success=True,
                    raw_content=item.get("raw_content"),
                    title=item.get("title"),
                )
            )
        for item in response.get("failed_results") or []:
            url = item.get("url") if isinstance(item, dict) else item
            if url and url not in succeeded_urls:
                results.append(
                    NormalizedExtractResult(
                        url=url,
                        success=False,
                        error=(item.get("error") if isinstance(item, dict) else "extraction failed"),
                    )
                )
        return results
