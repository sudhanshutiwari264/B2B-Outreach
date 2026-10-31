import urllib.robotparser
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx

from app.config import Settings, get_settings
from app.logging_config import get_logger
from app.research.url_safety import UnsafeURLError, validate_url_is_safe

logger = get_logger(__name__)

MAX_REDIRECTS = 5

_USER_AGENT = "OutreachIntelligenceBot/1.0 (+research; respects robots.txt)"


@dataclass
class FetchResult:
    url: str
    final_url: Optional[str]
    success: bool
    status_code: Optional[int]
    content_type: Optional[str]
    raw_bytes: Optional[bytes]
    error: Optional[str]
    robots_blocked: bool = False


async def _check_robots_allowed(url: str, client: httpx.AsyncClient) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        validate_url_is_safe(robots_url)
        resp = await client.get(robots_url, timeout=5.0)
        if resp.status_code >= 400:
            return True
        parser = urllib.robotparser.RobotFileParser()
        parser.parse(resp.text.splitlines())
        return parser.can_fetch(_USER_AGENT, url)
    except Exception:  # noqa: BLE001
        return True


async def fetch_url(url: str, *, settings: Optional[Settings] = None) -> FetchResult:
    """Fetch a URL with SSRF protection, safe manual redirect handling, timeouts, robots.txt
    respect, and a hard cap on response size. Never follows redirects blindly - every hop
    is re-validated against the SSRF allowlist before being requested.
    """
    settings = settings or get_settings()

    try:
        validate_url_is_safe(url)
    except UnsafeURLError as exc:
        return FetchResult(
            url=url, final_url=None, success=False, status_code=None,
            content_type=None, raw_bytes=None, error=str(exc),
        )

    current_url = url
    async with httpx.AsyncClient(
        follow_redirects=False,
        timeout=settings.http_timeout_seconds,
        headers={"User-Agent": _USER_AGENT},
    ) as client:
        if not await _check_robots_allowed(current_url, client):
            return FetchResult(
                url=url, final_url=current_url, success=False, status_code=None,
                content_type=None, raw_bytes=None, error="Disallowed by robots.txt",
                robots_blocked=True,
            )

        for _ in range(MAX_REDIRECTS + 1):
            try:
                response = await client.get(current_url)
            except httpx.TimeoutException as exc:
                return FetchResult(
                    url=url, final_url=current_url, success=False, status_code=None,
                    content_type=None, raw_bytes=None, error=f"Timeout: {exc}",
                )
            except httpx.HTTPError as exc:
                return FetchResult(
                    url=url, final_url=current_url, success=False, status_code=None,
                    content_type=None, raw_bytes=None, error=f"HTTP error: {exc}",
                )

            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    return FetchResult(
                        url=url, final_url=current_url, success=False,
                        status_code=response.status_code, content_type=None,
                        raw_bytes=None, error="Redirect with no Location header",
                    )
                next_url = httpx.URL(current_url).join(location)
                try:
                    validate_url_is_safe(str(next_url))
                except UnsafeURLError as exc:
                    return FetchResult(
                        url=url, final_url=str(next_url), success=False,
                        status_code=response.status_code, content_type=None,
                        raw_bytes=None, error=f"Unsafe redirect target: {exc}",
                    )
                current_url = str(next_url)
                continue

            content_type = response.headers.get("content-type")
            body = response.content[: settings.max_content_bytes]
            return FetchResult(
                url=url,
                final_url=current_url,
                success=response.status_code < 400,
                status_code=response.status_code,
                content_type=content_type,
                raw_bytes=body,
                error=None if response.status_code < 400 else f"HTTP {response.status_code}",
            )

    return FetchResult(
        url=url, final_url=current_url, success=False, status_code=None,
        content_type=None, raw_bytes=None, error="Too many redirects",
    )
