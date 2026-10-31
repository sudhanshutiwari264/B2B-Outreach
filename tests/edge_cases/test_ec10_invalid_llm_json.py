from unittest.mock import AsyncMock, MagicMock

from app.config import Settings
from app.integrations.tarqa_client import TarqaClient
from app.intelligence.signal_extractor import extract_signals_from_source
from app.models.enums import EvidenceType, ExtractionStatus, SourceType, VerificationStatus
from app.research.source_validator import ValidatedSource
from app.schemas.prospect import ProspectCreate


def _completion_with_content(content: str):
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


async def test_invalid_llm_json_never_produces_fabricated_signals():
    """EC-10: the LLM persistently returns malformed JSON. extract_signals_from_source
    must catch the validation failure and report insufficient_evidence, never returning
    fabricated signal data."""
    settings = Settings(tarqa_api_key="fake", tarqa_base_url="https://fake.example.com/api", tarqa_model="fake-model")
    client = TarqaClient(settings)
    client._sdk = MagicMock()
    client._sdk.chat = MagicMock()
    client._sdk.chat.completions = MagicMock()
    client._sdk.chat.completions.create = AsyncMock(
        return_value=_completion_with_content("this is not json at all, sorry")
    )

    prospect = ProspectCreate(name="Jane Doe", company="Acme Corp", designation="VP of Engineering")
    source = ValidatedSource(
        url="https://example.com/article",
        normalized_url="https://example.com/article",
        title="Acme news",
        domain="example.com",
        source_type=SourceType.COMPANY_NEWS,
        evidence_type=EvidenceType.FULL_PAGE,
        content="Acme Corp announced a new product today, said VP of Engineering Jane Doe.",
        content_hash="abc123",
        published_at=None,
        extraction_status=ExtractionStatus.SUCCESS,
        extraction_error=None,
        verification_status=VerificationStatus.PENDING,
    )

    outcome = await extract_signals_from_source(client, prospect, "source-1", source)

    assert outcome.signals == []
    assert outcome.insufficient_evidence is True
    assert outcome.error is not None
