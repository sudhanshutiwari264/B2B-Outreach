import asyncio
from urllib.parse import urlparse

import trafilatura

from app.config import Settings, get_settings
from app.integrations.tavily_client import TavilyClient
from app.logging_config import get_logger
from app.research.content_cleaner import (
    clean_text,
    compute_content_hash,
    extract_published_date_from_html,
    extract_title_from_html,
)
from app.research.schemas import ExtractedContent
from app.research.url_crawler import fetch_url

logger = get_logger(__name__)

RESTRICTED_DOMAINS = {"linkedin.com", "www.linkedin.com"}


def _domain_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def _is_restricted(url: str) -> bool:
    domain = _domain_of(url)
    return any(domain == d or domain.endswith("." + d) for d in RESTRICTED_DOMAINS)


async def _extract_locally(url: str, settings: Settings) -> ExtractedContent:
    """Fallback extraction for URLs Tavily Extract couldn't handle: fetch with SSRF-safe
    crawler, then try trafilatura first (purpose-built article extraction), falling back
    to a BeautifulSoup text dump if trafilatura finds nothing usable.
    """
    fetch_result = await fetch_url(url, settings=settings)
    if not fetch_result.success or not fetch_result.raw_bytes:
        return ExtractedContent(
            url=url, success=False, extraction_method="local_fetch", error=fetch_result.error
        )

    html = fetch_result.raw_bytes.decode("utf-8", errors="replace")

    text = trafilatura.extract(html, favor_recall=True)
    method = "trafilatura"
    if not text or len(text.strip()) < 50:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        method = "beautifulsoup"

    if not text or len(text.strip()) < 30:
        return ExtractedContent(
            url=url, success=False, extraction_method=method,
            error="Extracted content too short to be useful",
        )

    cleaned = clean_text(text)
    return ExtractedContent(
        url=url,
        success=True,
        title=extract_title_from_html(html),
        text=cleaned,
        published_at=extract_published_date_from_html(html),
        content_hash=compute_content_hash(cleaned),
        extraction_method=method,
    )


async def extract_content_for_urls(
    tavily: TavilyClient,
    urls: list[str],
    *,
    settings: Settings | None = None,
) -> list[ExtractedContent]:
    """Extract full-page content for the given URLs.

    - LinkedIn URLs are never crawled; they are marked restricted and left as search-snippet
      evidence only (EC-05).
    - For everything else: try Tavily Extract first (batched); for URLs Tavily fails on,
      fall back to our own SSRF-safe fetch + trafilatura/BeautifulSoup extraction (section 7).
    - Local fallback extraction is bounded by MAX_CONCURRENT_EXTRACTIONS.
    """
    settings = settings or get_settings()

    restricted = [u for u in urls if _is_restricted(u)]
    crawlable = [u for u in urls if u not in restricted]

    results: dict[str, ExtractedContent] = {
        u: ExtractedContent(
            url=u, success=False, restricted=True,
            error="LinkedIn content is access-restricted; using search snippet evidence only",
        )
        for u in restricted
    }

    if not crawlable:
        return list(results.values())

    tavily_results = []
    if tavily.is_configured:
        try:
            tavily_results = await tavily.extract_urls(crawlable)
        except Exception as exc:  # noqa: BLE001
            logger.warning("content_extractor.tavily_extract_failed", error=str(exc))
            tavily_results = []

    tavily_by_url = {r.url: r for r in tavily_results}
    need_local_fallback: list[str] = []

    for url in crawlable:
        tr = tavily_by_url.get(url)
        if tr and tr.success and tr.raw_content and len(tr.raw_content.strip()) >= 30:
            cleaned = clean_text(tr.raw_content)
            results[url] = ExtractedContent(
                url=url,
                success=True,
                title=tr.title,
                text=cleaned,
                content_hash=compute_content_hash(cleaned),
                extraction_method="tavily_extract",
            )
        else:
            need_local_fallback.append(url)

    if need_local_fallback:
        semaphore = asyncio.Semaphore(settings.max_concurrent_extractions)

        async def _bounded(u: str) -> ExtractedContent:
            async with semaphore:
                return await _extract_locally(u, settings)

        local_results = await asyncio.gather(*(_bounded(u) for u in need_local_fallback))
        for r in local_results:
            results[r.url] = r

    return list(results.values())
