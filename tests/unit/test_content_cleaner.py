from app.research.content_cleaner import (
    clean_text,
    compute_content_hash,
    extract_published_date_from_html,
    extract_title_from_html,
)


def test_clean_text_collapses_whitespace_and_bounds_length():
    raw = "Hello   world\n\n\n\nmore text" + ("x" * 25_000)
    cleaned = clean_text(raw)
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned
    assert len(cleaned) <= 20_000


def test_compute_content_hash_is_stable_across_whitespace_variants():
    a = compute_content_hash("Hello   World")
    b = compute_content_hash("hello world")
    c = compute_content_hash("Totally different text")
    assert a == b
    assert a != c


def test_extract_published_date_from_html_meta_tag():
    html = '<html><head><meta property="article:published_time" content="2026-05-10T10:00:00Z"></head></html>'
    assert extract_published_date_from_html(html) == "2026-05-10T10:00:00Z"


def test_extract_published_date_from_html_time_tag_fallback():
    html = "<html><body><time datetime='2025-01-01'>Jan 1</time></body></html>"
    assert extract_published_date_from_html(html) == "2025-01-01"


def test_extract_published_date_from_html_missing_returns_none():
    assert extract_published_date_from_html("<html><body>no dates here</body></html>") is None


def test_extract_title_from_html_prefers_title_tag():
    html = "<html><head><title>My Article</title></head></html>"
    assert extract_title_from_html(html) == "My Article"


def test_extract_title_from_html_og_title_fallback():
    html = '<html><head><meta property="og:title" content="OG Title"></head></html>'
    assert extract_title_from_html(html) == "OG Title"
