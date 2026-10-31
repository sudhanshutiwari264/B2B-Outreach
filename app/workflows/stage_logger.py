import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import StageStatus
from app.models.log import ExecutionLog
from app.resilience.error_handler import safe_error_message


class StageContext:
    def __init__(self, log: ExecutionLog):
        self._log = log
        self.output_metadata: dict = {}

    def set_output(self, **kwargs) -> None:
        self.output_metadata.update(kwargs)


@asynccontextmanager
async def stage(db: AsyncSession, execution_id: uuid.UUID, stage_name: str):
    """Persist a started/success/failed ExecutionLog row around a workflow stage,
    committing at each transition (not just flushing).

    This matters beyond logging correctness: the whole workflow runs as one long-lived
    background task holding a single AsyncSession. If stage boundaries only flushed,
    every row written during the run (logs, sources, signals, drafts) would stay
    invisible to every other DB session - including the API handlers the frontend polls -
    until the final commit at the very end. For a multi-minute execution that makes the
    UI look frozen/broken even though work is progressing. Committing per stage makes
    results stream in as they're produced.

    Exceptions raised inside the `with` block are recorded (status=failed, redacted
    error message) and re-raised so the caller can decide how to route the execution,
    satisfying section 4's "every stage must have ... error handling ... logging ...
    timing information" requirement uniformly for every stage.
    """
    started_at = datetime.now(timezone.utc)
    log = ExecutionLog(
        execution_id=execution_id,
        stage_name=stage_name,
        status=StageStatus.STARTED,
        started_at=started_at,
    )
    db.add(log)
    await db.commit()

    ctx = StageContext(log)
    t0 = time.monotonic()
    try:
        yield ctx
    except Exception as exc:  # noqa: BLE001
        log.status = StageStatus.FAILED
        log.error_message = safe_error_message(exc)
        log.ended_at = datetime.now(timezone.utc)
        log.duration_ms = int((time.monotonic() - t0) * 1000)
        log.output_metadata = ctx.output_metadata or None
        await db.commit()
        raise
    else:
        log.status = StageStatus.SUCCESS
        log.ended_at = datetime.now(timezone.utc)
        log.duration_ms = int((time.monotonic() - t0) * 1000)
        log.output_metadata = ctx.output_metadata or None
        await db.commit()
