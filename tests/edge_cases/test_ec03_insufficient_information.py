from app.models.enums import ExecutionStatus
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution, get_sample_prospect
from tests.fakes import UnconfiguredTarqaClient, UnconfiguredTavilyClient


async def test_insufficient_prospect_information_stops_before_research(db_session):
    """EC-03: a bare first name with no surname cannot be uniquely identified. The system
    must refuse to guess and must not perform any research at all - proven here by handing
    it clients that are not configured; if research were attempted it would raise."""
    prospect_dict = get_sample_prospect("insufficient_prospect_information")
    _, execution = await create_prospect_and_execution(db_session, prospect_dict)

    await run_prospect_workflow(
        db_session, execution.id,
        tavily=UnconfiguredTavilyClient(), tarqa=UnconfiguredTarqaClient(),
    )

    await db_session.refresh(execution)
    assert execution.status == ExecutionStatus.INSUFFICIENT_DATA
    assert execution.failure_reason is not None
    assert execution.result_summary["stage_stopped_at"] == "input_validation"
