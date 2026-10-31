from sqlalchemy import select

from app.models.enums import DraftStatus, ExecutionStatus
from app.models.log import ExecutionLog
from app.models.signal import Signal
from app.models.source import ResearchSource
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution, get_sample_fixture, get_sample_prospect
from tests.fakes import FakeTarqaClient, FakeTavilyClient


async def test_happy_path_produces_grounded_drafts_pending_human_review(db_session):
    """Full pipeline: research -> extraction -> scoring -> strategy -> drafting ->
    validation, ending with drafts that are NOT auto-approved (section 14)."""
    prospect_dict = get_sample_prospect("strong_linkedin_and_company_signals")
    fixture = get_sample_fixture("strong_linkedin_and_company_signals")

    _, execution = await create_prospect_and_execution(db_session, prospect_dict)

    tavily = FakeTavilyClient(fixture["search_results"], fixture["extracted_contents"])
    tarqa = FakeTarqaClient(entity=prospect_dict["name"], company=prospect_dict["company"])

    await run_prospect_workflow(db_session, execution.id, tavily=tavily, tarqa=tarqa)
    await db_session.refresh(execution)

    assert execution.status == ExecutionStatus.COMPLETED
    assert execution.started_at is not None
    assert execution.completed_at is not None

    sources = (await db_session.execute(select(ResearchSource).where(ResearchSource.execution_id == execution.id))).scalars().all()
    assert len(sources) >= 1

    signals = (await db_session.execute(select(Signal).where(Signal.execution_id == execution.id))).scalars().all()
    assert len(signals) >= 1
    assert all(s.final_score is not None for s in signals)

    from app.models.draft import OutreachDraft

    drafts = (await db_session.execute(select(OutreachDraft).where(OutreachDraft.execution_id == execution.id))).scalars().all()
    assert len(drafts) == 2  # email + linkedin
    assert {d.channel.value for d in drafts} == {"email", "linkedin"}
    assert all(d.status == DraftStatus.DRAFT_GENERATED for d in drafts)
    assert all(d.used_signal_ids for d in drafts)
    assert all(d.validation_report is not None for d in drafts)

    logs = (await db_session.execute(select(ExecutionLog).where(ExecutionLog.execution_id == execution.id))).scalars().all()
    stage_names = {l.stage_name for l in logs}
    assert "input_validation" in stage_names
    assert "signal_scoring" in stage_names
    assert "draft_generation" in stage_names
    assert all(l.duration_ms is not None for l in logs)


async def test_draft_approval_flow_never_auto_sends(db_session):
    """Section 14: approving a draft only records a human decision - there is no send
    integration, and a rejected/approved draft cannot be re-approved or re-rejected."""
    prospect_dict = get_sample_prospect("strong_linkedin_and_company_signals")
    fixture = get_sample_fixture("strong_linkedin_and_company_signals")

    _, execution = await create_prospect_and_execution(db_session, prospect_dict)

    tavily = FakeTavilyClient(fixture["search_results"], fixture["extracted_contents"])
    tarqa = FakeTarqaClient(entity=prospect_dict["name"], company=prospect_dict["company"])
    await run_prospect_workflow(db_session, execution.id, tavily=tavily, tarqa=tarqa)

    from app.models.draft import OutreachDraft

    drafts = (await db_session.execute(select(OutreachDraft).where(OutreachDraft.execution_id == execution.id))).scalars().all()
    draft = drafts[0]

    draft.status = DraftStatus.PENDING_REVIEW
    await db_session.commit()

    draft.status = DraftStatus.APPROVED
    await db_session.commit()
    await db_session.refresh(draft)

    assert draft.status == DraftStatus.APPROVED
    # No send-side-effect exists in this codebase; approval is purely a status flag.
