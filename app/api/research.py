import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal, get_db
from app.logging_config import get_logger
from app.models.execution import Execution
from app.models.prospect import Prospect
from app.models.signal import Signal
from app.models.source import ResearchSource
from app.models.enums import ExecutionStatus
from app.schemas.execution import ExecutionRead, ResearchRunAccepted, ResearchRunRequest
from app.schemas.signal import SignalRead
from app.schemas.source import SourceRead
from app.workflows.prospect_workflow import run_prospect_workflow

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/research", tags=["research"])


async def _run_workflow_background(execution_id: uuid.UUID) -> None:
    """Background tasks must open their own DB session - the request-scoped session from
    Depends(get_db) is closed as soon as the HTTP response is sent."""
    async with AsyncSessionLocal() as db:
        try:
            await run_prospect_workflow(db, execution_id)
        except Exception:  # noqa: BLE001
            logger.exception("research.background_workflow_crashed", execution_id=str(execution_id))


@router.post("/run", response_model=ResearchRunAccepted, status_code=status.HTTP_202_ACCEPTED)
async def run_research(
    payload: ResearchRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResearchRunAccepted:
    prospect = await db.get(Prospect, payload.prospect_id)
    if prospect is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found")

    if payload.idempotency_key:
        existing = await db.execute(
            select(Execution).where(Execution.idempotency_key == payload.idempotency_key)
        )
        existing_execution = existing.scalar_one_or_none()
        if existing_execution is not None:
            return ResearchRunAccepted(
                execution_id=existing_execution.id,
                status=existing_execution.status,
                message="An execution with this idempotency key already exists",
            )

    execution = Execution(
        prospect_id=prospect.id,
        status=ExecutionStatus.QUEUED,
        idempotency_key=payload.idempotency_key,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    background_tasks.add_task(_run_workflow_background, execution.id)

    return ResearchRunAccepted(
        execution_id=execution.id,
        status=execution.status,
        message="Research execution queued. Poll GET /api/v1/research/{execution_id} for status.",
    )


@router.get("/{execution_id}", response_model=ExecutionRead)
async def get_execution_status(execution_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Execution:
    execution = await db.get(Execution, execution_id)
    if execution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return execution


@router.get("/{execution_id}/sources", response_model=list[SourceRead])
async def get_execution_sources(execution_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[ResearchSource]:
    result = await db.execute(
        select(ResearchSource).where(ResearchSource.execution_id == execution_id)
    )
    return list(result.scalars().all())


@router.get("/{execution_id}/signals", response_model=list[SignalRead])
async def get_execution_signals(execution_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[Signal]:
    result = await db.execute(
        select(Signal).where(Signal.execution_id == execution_id).order_by(Signal.final_score.desc())
    )
    return list(result.scalars().all())
