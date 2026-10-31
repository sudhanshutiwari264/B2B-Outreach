from sqlalchemy import select

from app.models.draft import OutreachDraft
from app.models.enums import (
    DraftStatus,
    EvidenceType,
    ExecutionStatus,
    OutreachChannel,
    SignalType,
    SourceType,
    VerificationStatus,
)
from app.models.execution import Execution
from app.models.prospect import Prospect
from app.models.signal import Signal
from app.models.source import ResearchSource


async def test_full_entity_chain_persists_and_round_trips(db_session):
    prospect = Prospect(name="Jane Doe", company="Acme Corp", designation="VP of Engineering")
    db_session.add(prospect)
    await db_session.flush()

    execution = Execution(prospect_id=prospect.id, status=ExecutionStatus.RUNNING)
    db_session.add(execution)
    await db_session.flush()

    source = ResearchSource(
        execution_id=execution.id,
        url="https://example.com/article",
        normalized_url="https://example.com/article",
        source_type=SourceType.COMPANY_NEWS,
        evidence_type=EvidenceType.FULL_PAGE,
        content="Acme Corp raised a Series B.",
        verification_status=VerificationStatus.PENDING,
    )
    db_session.add(source)
    await db_session.flush()

    signal = Signal(
        execution_id=execution.id,
        source_id=source.id,
        signal_type=SignalType.FUNDING,
        description="Acme Corp raised a Series B",
        entity="Jane Doe",
        company="Acme Corp",
        evidence_excerpt="Acme Corp raised a Series B.",
        relevance_reason="Funding often means growth",
        confidence_score=90,
        final_score=85.0,
    )
    db_session.add(signal)
    await db_session.flush()

    draft = OutreachDraft(
        execution_id=execution.id,
        channel=OutreachChannel.EMAIL,
        subject="Congrats on the raise",
        body="Hi Jane, congrats on the Series B...",
        used_signal_ids=[str(signal.id)],
        used_source_ids=[str(source.id)],
        status=DraftStatus.DRAFT_GENERATED,
    )
    db_session.add(draft)
    await db_session.commit()

    fetched_execution = await db_session.get(Execution, execution.id)
    assert fetched_execution.prospect_id == prospect.id

    sources = (await db_session.execute(select(ResearchSource).where(ResearchSource.execution_id == execution.id))).scalars().all()
    assert len(sources) == 1

    signals = (await db_session.execute(select(Signal).where(Signal.source_id == source.id))).scalars().all()
    assert len(signals) == 1

    drafts = (await db_session.execute(select(OutreachDraft).where(OutreachDraft.execution_id == execution.id))).scalars().all()
    assert drafts[0].used_signal_ids == [str(signal.id)]


async def test_deleting_execution_cascades_to_children(db_session):
    prospect = Prospect(name="John Smith", company="Beta Inc", designation="CTO")
    db_session.add(prospect)
    await db_session.flush()

    execution = Execution(prospect_id=prospect.id, status=ExecutionStatus.COMPLETED)
    db_session.add(execution)
    await db_session.flush()

    source = ResearchSource(
        execution_id=execution.id, url="https://x.com/a", normalized_url="https://x.com/a",
        source_type=SourceType.OTHER, evidence_type=EvidenceType.SEARCH_SNIPPET,
        verification_status=VerificationStatus.PENDING,
    )
    db_session.add(source)
    await db_session.commit()

    await db_session.delete(execution)
    await db_session.commit()

    remaining = (await db_session.execute(select(ResearchSource).where(ResearchSource.execution_id == execution.id))).scalars().all()
    assert remaining == []
