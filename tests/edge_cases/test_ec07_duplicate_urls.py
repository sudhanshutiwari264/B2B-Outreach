from sqlalchemy import select

from app.models.enums import EvidenceType
from app.models.source import ResearchSource
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution, get_sample_fixture, get_sample_prospect
from tests.fakes import FakeTarqaClient, FakeTavilyClient


async def test_duplicate_syndicated_urls_collapse_to_one_source(db_session):
    """EC-07: the same announcement appears on two different (mirrored) URLs with identical
    content. Content-hash deduplication must collapse them into a single FULL_PAGE source."""
    prospect_dict = get_sample_prospect("duplicate_search_results")
    fixture = get_sample_fixture("duplicate_search_results")

    _, execution = await create_prospect_and_execution(db_session, prospect_dict)

    tavily = FakeTavilyClient(fixture["search_results"], fixture["extracted_contents"])
    tarqa = FakeTarqaClient(entity=prospect_dict["name"], company=prospect_dict["company"])

    await run_prospect_workflow(db_session, execution.id, tavily=tavily, tarqa=tarqa)

    sources = (
        await db_session.execute(select(ResearchSource).where(ResearchSource.execution_id == execution.id))
    ).scalars().all()

    full_page_sources = [s for s in sources if s.evidence_type == EvidenceType.FULL_PAGE]
    assert len(full_page_sources) == 1, "duplicate content across mirrored URLs should collapse to one source"
