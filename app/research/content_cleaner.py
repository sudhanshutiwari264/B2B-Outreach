import hashlib
import re
from typing import Optional

from bs4 import BeautifulSoup

MAX_CLEAN_TEXT_CHARS = 20_000

_DATE_META_NAMES = [
    "article:published_time",
    "og:updated_time",
    "og:article:published_time",
    "datePublished",
    "publish-date",
    "publishdate",
    "date",
]


def clean_text(text: str) -> str:
    """Collapse whitespace and bound length so downstream LLM calls stay within budget."""
    if not text:
        return ""
    collapsed = re.sub(r"[ \t]+", " ", text)
    collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
    collapsed = collapsed.strip()
    return collapsed[:MAX_CLEAN_TEXT_CHARS]


def compute_content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text or "").strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_published_date_from_html(html: str) -> Optional[str]:
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:  # noqa: BLE001
        return None

    for name in _DATE_META_NAMES:
        tag = soup.find("meta", attrs={"property": name}) or soup.find(
            "meta", attrs={"name": name}
        )
        if tag and tag.get("content"):
            return tag["content"].strip()

    time_tag = soup.find("time")
    if time_tag:
        if time_tag.get("datetime"):
            return time_tag["datetime"].strip()
        if time_tag.text:
            return time_tag.text.strip()

    return None


def extract_title_from_html(html: str) -> Optional[str]:
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:  # noqa: BLE001
        return None
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        return og_title["content"].strip()
    return None
