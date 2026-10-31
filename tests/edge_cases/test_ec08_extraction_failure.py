from sqlalchemy import select

from app.models.enums import EvidenceType, ExecutionStatus, ExtractionStatus
from app.models.source import ResearchSource
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution
from tests.fakes import FakeTarqaClient, FakeTavilyClient

PROSPECT = {"name": "Taylor Winters", "company": "Cascade Freight Logistics", "designation": "VP Operations"}

SEARCH_RESULTS = [
    {
        "url": "https://www.freightnews.example.com/cascade-expansion",
        "title": "Cascade Freight Logistics expands fleet",
        "snippet": "Cascade Freight Logistics announced a major fleet expansion to meet rising demand, VP Operations Taylor Winters said.",
        "query": "q", "category_hint": "company_news",
    }
]


async def test_extraction_failure_falls_back_to_snippet_and_pipeline_continues(db_session):
    """EC-08: the webpage extraction (both Tavily Extract and the local fallback) fails
    for every URL. The pipeline must not crash - it should fall back to search-snippet
    evidence and keep going."""
    _, execution = await create_prospect_and_execution(db_session, PROSPECT)

    # No extracted_contents fixture entries at all => every extraction attempt "fails".
    tavily = FakeTavilyClient(SEARCH_RESULTS, extracted_contents=[])
    tarqa = FakeTarqaClient(entity=PROSPECT["name"], company=PROSPECT["company"])

    await run_prospect_workflow(db_session, execution.id, tavily=tavily, tarqa=tarqa)
    await db_session.refresh(execution)

    assert execution.status != ExecutionStatus.FAILED

    sources = (
        await db_session.execute(select(ResearchSource).where(ResearchSource.execution_id == execution.id))
    ).scalars().all()
    assert sources
    assert all(s.extraction_status == ExtractionStatus.FAILED for s in sources)
    assert all(s.evidence_type == EvidenceType.SEARCH_SNIPPET for s in sources)
    assert all(s.content for s in sources), "snippet content must still be usable as evidence"
