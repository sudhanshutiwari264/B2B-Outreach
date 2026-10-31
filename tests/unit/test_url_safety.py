import pytest

from app.research.url_safety import UnsafeURLError, normalize_url, validate_url_is_safe


def test_normalize_url_strips_tracking_params_and_fragment():
    a = normalize_url("https://Example.com/Article/?utm_source=x&id=1#section2")
    b = normalize_url("https://example.com/Article?id=1")
    assert a == b


def test_normalize_url_strips_default_ports():
    assert normalize_url("https://example.com:443/path") == normalize_url("https://example.com/path")


def test_normalize_url_dedupes_equivalent_urls():
    urls = [
        "https://example.com/news/story?utm_campaign=foo",
        "https://example.com/news/story/",
        "https://EXAMPLE.com/news/story",
    ]
    normalized = {normalize_url(u) for u in urls}
    assert len(normalized) == 1


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8000/admin",
        "http://127.0.0.1/secret",
        "http://0.0.0.0/",
        "http://169.254.169.254/latest/meta-data/",
        "ftp://example.com/file",
        "file:///etc/passwd",
    ],
)
def test_validate_url_is_safe_rejects_dangerous_targets(url):
    with pytest.raises(UnsafeURLError):
        validate_url_is_safe(url)


def test_validate_url_is_safe_rejects_unresolvable_host():
    with pytest.raises(UnsafeURLError):
        validate_url_is_safe("https://this-domain-should-not-resolve.invalid/")


def test_validate_url_is_safe_accepts_public_host():
    # example.com is a well-known public, non-private address.
    assert validate_url_is_safe("https://example.com/path") == "https://example.com/path"
