from sqlalchemy import select

from app.models.conflict import SignalConflict
from app.models.enums import ConflictType, ExecutionStatus, VerificationStatus
from app.models.signal import Signal
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution, get_sample_fixture, get_sample_prospect
from tests.fakes import FakeTarqaClient, FakeTavilyClient


async def test_conflicting_job_titles_are_disputed_and_excluded(db_session):
    """EC-02: sources disagree on the prospect's title. Both source records must survive,
    the affected signals must be marked disputed, and the execution must be routed to
    human review rather than silently picking one claim."""
    prospect_dict = get_sample_prospect("conflicting_job_information")
    fixture = get_sample_fixture("conflicting_job_information")

    _, execution = await create_prospect_and_execution(db_session, prospect_dict)

    tavily = FakeTavilyClient(fixture["search_results"], fixture["extracted_contents"])
    tarqa = FakeTarqaClient(entity=prospect_dict["name"], company=prospect_dict["company"])

    await run_prospect_workflow(db_session, execution.id, tavily=tavily, tarqa=tarqa)
    await db_session.refresh(execution)

    conflicts = (
        await db_session.execute(select(SignalConflict).where(SignalConflict.execution_id == execution.id))
    ).scalars().all()
    assert any(c.conflict_type == ConflictType.JOB_TITLE for c in conflicts)

    disputed_signal_ids = set()
    for c in conflicts:
        disputed_signal_ids.update(c.signal_ids)
    assert disputed_signal_ids, "expected at least one disputed signal id"

    signals = (
        await db_session.execute(select(Signal).where(Signal.execution_id == execution.id))
    ).scalars().all()
    disputed = [s for s in signals if str(s.id) in disputed_signal_ids]
    assert all(s.is_disputed for s in disputed)
    assert all(s.verification_status == VerificationStatus.DISPUTED for s in disputed)

    # Disputed signals must never be the ones used to ground an outreach draft.
    assert execution.status in (ExecutionStatus.NEEDS_REVIEW, ExecutionStatus.INSUFFICIENT_DATA)
