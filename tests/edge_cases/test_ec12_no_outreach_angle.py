from sqlalchemy import select

from app.models.draft import OutreachDraft
from app.models.enums import ExecutionStatus
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution, get_sample_fixture, get_sample_prospect
from tests.fakes import FakeTarqaClient, FakeTavilyClient


async def test_no_extractable_signal_returns_insufficient_evidence(db_session):
    """EC-12: sources were found and researched, but nothing extractable rises to the bar
    for a personalized outreach angle. The system must return insufficient_data and must
    not generate a draft, rather than forcing a weak/generic message."""
    prospect_dict = get_sample_prospect("strong_linkedin_and_company_signals")
    fixture = get_sample_fixture("strong_linkedin_and_company_signals")

    _, execution = await create_prospect_and_execution(db_session, prospect_dict)

    tavily = FakeTavilyClient(fixture["search_results"], fixture["extracted_contents"])
    tarqa = FakeTarqaClient(insufficient_evidence=True)

    await run_prospect_workflow(db_session, execution.id, tavily=tavily, tarqa=tarqa)
    await db_session.refresh(execution)

    assert execution.status == ExecutionStatus.INSUFFICIENT_DATA
    assert execution.failure_reason is not None

    drafts = (
        await db_session.execute(select(OutreachDraft).where(OutreachDraft.execution_id == execution.id))
    ).scalars().all()
    assert drafts == []
