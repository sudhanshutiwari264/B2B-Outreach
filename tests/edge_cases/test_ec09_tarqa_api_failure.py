from sqlalchemy import select

from app.models.enums import ExecutionStatus, StageStatus
from app.models.log import ExecutionLog
from app.models.signal import Signal
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution, get_sample_fixture, get_sample_prospect
from tests.fakes import FailingTarqaClient, FakeTavilyClient


async def test_persistent_tarqa_failure_is_recorded_without_fabricating_signals(db_session):
    """EC-09: Tarqa AI is completely unreachable. The workflow must not crash, must not
    invent signals, and must record the failure in the execution logs."""
    prospect_dict = get_sample_prospect("strong_linkedin_and_company_signals")
    fixture = get_sample_fixture("strong_linkedin_and_company_signals")

    _, execution = await create_prospect_and_execution(db_session, prospect_dict)

    tavily = FakeTavilyClient(fixture["search_results"], fixture["extracted_contents"])

    await run_prospect_workflow(db_session, execution.id, tavily=tavily, tarqa=FailingTarqaClient())
    await db_session.refresh(execution)

    assert execution.status != ExecutionStatus.FAILED
    assert execution.status == ExecutionStatus.INSUFFICIENT_DATA

    signals = (
        await db_session.execute(select(Signal).where(Signal.execution_id == execution.id))
    ).scalars().all()
    assert signals == [], "no signals must be fabricated when the LLM is unreachable"

    logs = (
        await db_session.execute(select(ExecutionLog).where(ExecutionLog.execution_id == execution.id))
    ).scalars().all()
    extraction_log = next(l for l in logs if l.stage_name == "signal_extraction")
    assert extraction_log.output_metadata["extraction_failures"] > 0
