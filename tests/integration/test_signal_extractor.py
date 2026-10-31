from app.intelligence.signal_extractor import extract_signals_from_source
from app.models.enums import EvidenceType, ExtractionStatus, SourceType, VerificationStatus
from app.research.source_validator import ValidatedSource
from app.schemas.prospect import ProspectCreate
from app.schemas.signal import ExtractedSignalLLM, SignalExtractionLLMResponse

SOURCE = ValidatedSource(
    url="https://example.com/article",
    normalized_url="https://example.com/article",
    title="Acme news",
    domain="example.com",
    source_type=SourceType.COMPANY_NEWS,
    evidence_type=EvidenceType.FULL_PAGE,
    content="Acme Corp announced a new product today, said VP of Engineering Jane Doe in a statement.",
    content_hash="hash1",
    published_at=None,
    extraction_status=ExtractionStatus.SUCCESS,
    extraction_error=None,
    verification_status=VerificationStatus.PENDING,
)

PROSPECT = ProspectCreate(name="Jane Doe", company="Acme Corp", designation="VP of Engineering")


class _StubTarqa:
    def __init__(self, response: SignalExtractionLLMResponse):
        self._response = response

    async def generate_structured_output(self, messages, response_model, **kwargs):
        return self._response


async def test_grounded_excerpt_is_kept():
    response = SignalExtractionLLMResponse(
        signals=[
            ExtractedSignalLLM(
                signal_type="product_development",
                description="Acme Corp announced a new product",
                entity="Jane Doe",
                company="Acme Corp",
                evidence_excerpt="Acme Corp announced a new product today",
                relevance_reason="Relevant to engineering leadership",
                confidence_score=85,
            )
        ]
    )
    outcome = await extract_signals_from_source(_StubTarqa(response), PROSPECT, "src-1", SOURCE)
    assert len(outcome.signals) == 1


async def test_ungrounded_excerpt_is_dropped():
    """Section 9: the LLM must only extract information supported by the provided
    content - a hallucinated excerpt that doesn't appear in the source must be dropped."""
    response = SignalExtractionLLMResponse(
        signals=[
            ExtractedSignalLLM(
                signal_type="funding",
                description="Acme Corp raised $500 million",
                entity="Jane Doe",
                company="Acme Corp",
                evidence_excerpt="Acme Corp closed a historic $500 million funding round led by Sequoia",
                relevance_reason="Huge funding event",
                confidence_score=95,
            )
        ]
    )
    outcome = await extract_signals_from_source(_StubTarqa(response), PROSPECT, "src-1", SOURCE)
    assert outcome.signals == []
    assert outcome.insufficient_evidence is True


async def test_source_with_no_content_skips_llm_call_entirely():
    empty_source = SOURCE.__class__(**{**SOURCE.__dict__, "content": None})

    class _ExplodingTarqa:
        async def generate_structured_output(self, *args, **kwargs):
            raise AssertionError("LLM must not be called for a source with no content")

    outcome = await extract_signals_from_source(_ExplodingTarqa(), PROSPECT, "src-1", empty_source)
    assert outcome.signals == []
    assert outcome.insufficient_evidence is True
