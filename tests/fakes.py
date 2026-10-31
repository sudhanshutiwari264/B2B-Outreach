"""Test doubles for TavilyClient / TarqaClient used by edge-case and end-to-end tests.

These implement just enough of the real clients' public interface for
app.workflows.prospect_workflow.run_prospect_workflow to exercise the full pipeline
without any live network/API calls, per section 20 ("unit tests must not require live
API credentials").
"""
import re

from app.integrations.schemas import NormalizedExtractResult, NormalizedSearchResult
from app.models.enums import SignalType
from app.schemas.draft import EmailDraftContent, LinkedInDraftContent
from app.schemas.signal import ExtractedSignalLLM, SignalExtractionLLMResponse

_KEYWORD_TO_SIGNAL_TYPE: list[tuple[re.Pattern, SignalType]] = [
    (re.compile(r"\b(raised|funding round|series [abc]|million in funding)\b", re.I), SignalType.FUNDING),
    (re.compile(r"\b(named|appointed|promoted|chief \w+ officer|ceo|coo|cfo|cto)\b", re.I), SignalType.JOB_CHANGE),
    (re.compile(r"\b(hiring|open roles|is hiring|job openings)\b", re.I), SignalType.HIRING),
    (re.compile(r"\b(partnership|partners with|teamed up)\b", re.I), SignalType.PARTNERSHIP),
    (re.compile(r"\b(launch(ed|es)?|new (product|platform|suite))\b", re.I), SignalType.PRODUCT_DEVELOPMENT),
    (re.compile(r"\b(expansion|expands|new office|new hub|new market)\b", re.I), SignalType.COMPANY_GROWTH),
    (re.compile(r"\b(layoffs|restructuring|challenges)\b", re.I), SignalType.BUSINESS_CHALLENGE),
    (re.compile(r"\b(interview|podcast|believes|discussed)\b", re.I), SignalType.THOUGHT_LEADERSHIP),
]


def _guess_signal_type_from_content(content: str) -> SignalType:
    for pattern, signal_type in _KEYWORD_TO_SIGNAL_TYPE:
        if pattern.search(content):
            return signal_type
    return SignalType.PROFESSIONAL_ACTIVITY


class FakeTavilyClient:
    """Returns the same fixed set of search results/extractions for every query, since the
    real query-generation fan-out (many queries per category) isn't what's under test here
    - downstream URL deduplication collapses the repeats exactly as it would in production.
    """

    def __init__(self, search_results: list[dict], extracted_contents: list[dict]):
        self._search_results = search_results
        self._extracted_by_url = {e["url"]: e for e in extracted_contents}

    @property
    def is_configured(self) -> bool:
        return True

    async def _search(self, query: str, *, category_hint: str, max_results: int = 5):
        # Each fixture result keeps its own authored category_hint rather than being
        # overwritten by whichever Tavily method/query happened to "find" it - the real
        # SDK wrapper does the same (category_hint reflects content, not call site).
        return [
            NormalizedSearchResult(
                url=r["url"], title=r.get("title"), snippet=r.get("snippet", ""),
                search_score=r.get("search_score"), published_date=r.get("published_date"),
                query=query, category_hint=r.get("category_hint", category_hint),
            )
            for r in self._search_results
        ][:max_results]

    async def search_web(self, query: str, *, category_hint: str = "other", max_results: int = 5, **kwargs):
        return await self._search(query, category_hint=category_hint, max_results=max_results)

    async def discover_linkedin_profile(self, query: str, *, max_results: int = 5):
        return await self._search(query, category_hint="linkedin_profile", max_results=max_results)

    async def discover_linkedin_posts(self, query: str, *, max_results: int = 5):
        return await self._search(query, category_hint="linkedin_post", max_results=max_results)

    async def search_company_news(self, query: str, *, max_results: int = 5):
        return await self._search(query, category_hint="company_news", max_results=max_results)

    async def search_company_hiring(self, query: str, *, max_results: int = 5):
        return await self._search(query, category_hint="hiring", max_results=max_results)

    async def search_funding(self, query: str, *, max_results: int = 5):
        return await self._search(query, category_hint="funding", max_results=max_results)

    async def extract_urls(self, urls: list[str]) -> list[NormalizedExtractResult]:
        results = []
        for u in urls:
            fixture = self._extracted_by_url.get(u)
            if fixture and fixture.get("success"):
                results.append(
                    NormalizedExtractResult(
                        url=u, success=True, raw_content=fixture.get("text"), title=fixture.get("title")
                    )
                )
            else:
                results.append(NormalizedExtractResult(url=u, success=False, error="no fixture content"))
        return results


class EmptyTavilyClient(FakeTavilyClient):
    """Simulates Tavily returning zero results for every query (EC-06)."""

    def __init__(self):
        super().__init__(search_results=[], extracted_contents=[])


class UnconfiguredTavilyClient:
    is_configured = False


class UnconfiguredTarqaClient:
    is_configured = False


class FailingTarqaClient:
    """Simulates Tarqa AI being persistently unreachable (EC-09): every call raises, and
    the workflow must record the failure and continue rather than fabricating signals."""

    is_configured = True

    async def generate_structured_output(self, messages, response_model, **kwargs):
        from app.integrations.tarqa_client import TarqaIntegrationError

        raise TarqaIntegrationError("simulated persistent Tarqa AI outage")


class FakeTarqaClient:
    """Deterministically "extracts" one grounded signal per source (derived straight from
    the source text handed to it) and returns template drafts, so the full pipeline -
    scoring, conflict detection, strategy, drafting, validation - runs on realistic,
    schema-correct data without hitting a real LLM.
    """

    def __init__(self, *, insufficient_evidence: bool = False, entity: str = "", company: str = ""):
        self._insufficient_evidence = insufficient_evidence
        self._entity = entity
        self._company = company

    @property
    def is_configured(self) -> bool:
        return True

    async def generate_structured_output(self, messages, response_model, **kwargs):
        if response_model is SignalExtractionLLMResponse:
            return self._fake_signal_extraction(messages)
        if response_model is EmailDraftContent:
            return self._fake_email_draft(messages)
        if response_model is LinkedInDraftContent:
            return self._fake_linkedin_draft(messages)
        raise NotImplementedError(f"FakeTarqaClient has no handler for {response_model}")

    def _fake_signal_extraction(self, messages) -> SignalExtractionLLMResponse:
        if self._insufficient_evidence:
            return SignalExtractionLLMResponse(signals=[], insufficient_evidence=True)

        user_content = messages[-1]["content"]
        match = re.search(
            r"<<<UNTRUSTED_WEBPAGE_CONTENT_START>>>\n(.*?)\n<<<UNTRUSTED_WEBPAGE_CONTENT_END>>>",
            user_content, re.DOTALL,
        )
        content = match.group(1).strip() if match else ""

        if not content:
            return SignalExtractionLLMResponse(signals=[], insufficient_evidence=True)

        excerpt = content[:120].strip()
        return SignalExtractionLLMResponse(
            signals=[
                ExtractedSignalLLM(
                    signal_type=_guess_signal_type_from_content(content),
                    description=excerpt[:200],
                    entity=self._entity or "Unknown",
                    company=self._company or None,
                    published_at=None,
                    evidence_excerpt=excerpt,
                    relevance_reason="Derived from fixture content for test purposes",
                    confidence_score=85,
                )
            ],
            insufficient_evidence=False,
        )

    def _fake_email_draft(self, messages) -> EmailDraftContent:
        user_content = messages[-1]["content"]
        excerpt_match = re.search(r'excerpt, source: [^)]*\):\n"(.*?)"', user_content)
        excerpt = excerpt_match.group(1) if excerpt_match else "the recent update"
        body = (
            f"Hi there, I noticed {excerpt} - that's a great signal for teams scaling "
            "fast. We help with exactly that kind of workflow automation challenge. "
            "Would you be open to a quick call next week?"
        )
        return EmailDraftContent(
            subject="Quick note on your recent update",
            opening="Hi there,",
            contextual_observation=excerpt,
            business_relevance="This usually means new operational demands.",
            value_proposition="Our platform helps teams automate exactly this kind of workflow.",
            call_to_action="Would you be open to a quick call next week?",
            body=body,
        )

    def _fake_linkedin_draft(self, messages) -> LinkedInDraftContent:
        user_content = messages[-1]["content"]
        excerpt_match = re.search(r'excerpt, source: [^)]*\):\n"(.*?)"', user_content)
        excerpt = excerpt_match.group(1) if excerpt_match else "the recent update"
        body = (
            f"Hi, saw {excerpt} - exciting stuff. We work on workflow automation for "
            "teams going through exactly this kind of growth. Worth a quick chat?"
        )
        return LinkedInDraftContent(
            opening="Hi,",
            professional_observation=excerpt,
            conversational_context="Teams usually need better tooling at this stage.",
            call_to_action="Worth a quick chat?",
            body=body,
        )
