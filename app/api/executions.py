import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.execution import Execution
from app.models.log import ExecutionLog
from app.schemas.execution import ExecutionLogRead, ExecutionRead

router = APIRouter(prefix="/api/v1/executions", tags=["executions"])


@router.get("", response_model=list[ExecutionRead])
async def list_executions(
    limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)
) -> list[Execution]:
    result = await db.execute(
        select(Execution).order_by(Execution.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all())


@router.get("/{execution_id}/logs", response_model=list[ExecutionLogRead])
async def get_execution_logs(execution_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[ExecutionLog]:
    execution = await db.get(Execution, execution_id)
    if execution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    result = await db.execute(
        select(ExecutionLog)
        .where(ExecutionLog.execution_id == execution_id)
        .order_by(ExecutionLog.started_at.asc())
    )
    return list(result.scalars().all())
