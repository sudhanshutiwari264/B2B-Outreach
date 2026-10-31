from typing import Optional

from pydantic import BaseModel, Field


class NormalizedSearchResult(BaseModel):
    """Common internal representation for anything discovered via web search.

    This is always SEARCH-SNIPPET evidence: a title + short content excerpt returned by
    the search engine, not the full page. It must never be treated as equivalent to a
    fully extracted page (see EvidenceType in app.models.enums).
    """

    url: str
    title: Optional[str] = None
    snippet: str = ""
    search_score: Optional[float] = None
    published_date: Optional[str] = None
    query: str = ""
    category_hint: str = "other"


class NormalizedExtractResult(BaseModel):
    """Common internal representation for a full-page content extraction attempt."""

    url: str
    success: bool
    raw_content: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None


class SearchQuerySpec(BaseModel):
    """A single generated search query plus metadata about its intent."""

    query: str
    category_hint: str = Field(description="e.g. linkedin, company_news, funding, hiring, professional")
    max_results: int = 5
