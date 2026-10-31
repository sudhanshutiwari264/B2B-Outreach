from sqlalchemy import select

from app.models.enums import ExecutionStatus, SourceType
from app.models.signal import Signal
from app.models.source import ResearchSource
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution, get_sample_fixture, get_sample_prospect
from tests.fakes import FakeTarqaClient, FakeTavilyClient


async def test_no_linkedin_activity_falls_back_to_company_news(db_session):
    """EC-01: no LinkedIn evidence is available, but company news exists. The system must
    still produce a draft grounded in that alternative evidence, and must never fabricate
    LinkedIn activity that was never found."""
    prospect_dict = get_sample_prospect("no_recent_linkedin_activity")
    fixture = get_sample_fixture("no_recent_linkedin_activity")

    _, execution = await create_prospect_and_execution(db_session, prospect_dict)

    tavily = FakeTavilyClient(fixture["search_results"], fixture["extracted_contents"])
    tarqa = FakeTarqaClient(entity=prospect_dict["name"], company=prospect_dict["company"])

    await run_prospect_workflow(db_session, execution.id, tavily=tavily, tarqa=tarqa)

    await db_session.refresh(execution)
    assert execution.status in (ExecutionStatus.COMPLETED, ExecutionStatus.PARTIAL)

    sources = (
        await db_session.execute(select(ResearchSource).where(ResearchSource.execution_id == execution.id))
    ).scalars().all()
    assert not any(s.source_type in (SourceType.LINKEDIN_PROFILE, SourceType.LINKEDIN_POST) for s in sources)

    signals = (
        await db_session.execute(select(Signal).where(Signal.execution_id == execution.id))
    ).scalars().all()
    assert len(signals) >= 1
