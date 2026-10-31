import ipaddress
import socket
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

ALLOWED_SCHEMES = {"http", "https"}

_TRACKING_PARAM_PREFIXES = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid", "ref_src")

_BLOCKED_HOSTNAMES = {"localhost", "0.0.0.0", "metadata.google.internal"}


class UnsafeURLError(Exception):
    """Raised when a URL fails SSRF/protocol/destination safety checks."""


def normalize_url(url: str) -> str:
    """Canonicalize a URL for deduplication purposes (EC-07).

    Lower-cases scheme/host, strips fragments, default ports, trailing slashes, and
    known tracking query params, and sorts remaining query params.
    """
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    if netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not any(k.lower().startswith(p) for p in _TRACKING_PARAM_PREFIXES)
    ]
    query_pairs.sort()
    query = urlencode(query_pairs)

    return urlunparse((scheme, netloc, path, "", query, ""))


def _is_private_or_reserved(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_url_is_safe(url: str) -> str:
    """Validate protocol and resolve+check the destination IP to block SSRF.

    Returns the validated URL on success, raises UnsafeURLError otherwise. Must be called
    again on every redirect hop, not just the original URL, since DNS/redirects can point
    to internal infrastructure after the first check passes.
    """
    parsed = urlparse(url)

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeURLError(f"Disallowed scheme: {parsed.scheme!r}")

    hostname = parsed.hostname
    if not hostname:
        raise UnsafeURLError("URL has no hostname")

    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise UnsafeURLError(f"Blocked hostname: {hostname}")

    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"DNS resolution failed for {hostname}: {exc}") from exc

    if not addr_infos:
        raise UnsafeURLError(f"No addresses resolved for {hostname}")

    for family, _, _, _, sockaddr in addr_infos:
        ip_str = sockaddr[0]
        if _is_private_or_reserved(ip_str):
            raise UnsafeURLError(
                f"URL resolves to a private/reserved address ({ip_str}), refusing to fetch"
            )

    return url
