from app.models.enums import ExecutionStatus
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution
from tests.fakes import EmptyTavilyClient, FakeTarqaClient

PROSPECT = {"name": "Nobody Findable", "company": "Totally Obscure Co", "designation": "Manager"}


async def test_zero_search_results_yields_insufficient_data(db_session):
    """EC-06: Tavily returns nothing for any query variation - the system must report
    insufficient_data rather than fabricating research results."""
    _, execution = await create_prospect_and_execution(db_session, PROSPECT)

    await run_prospect_workflow(
        db_session, execution.id, tavily=EmptyTavilyClient(), tarqa=FakeTarqaClient()
    )

    await db_session.refresh(execution)
    assert execution.status == ExecutionStatus.INSUFFICIENT_DATA
    assert execution.result_summary["stage_stopped_at"] == "url_deduplication"
