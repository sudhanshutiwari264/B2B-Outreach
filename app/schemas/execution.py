import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ExecutionStatus, StageStatus


class ResearchRunRequest(BaseModel):
    prospect_id: uuid.UUID
    idempotency_key: Optional[str] = Field(default=None, max_length=200)


class ExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prospect_id: uuid.UUID
    status: ExecutionStatus
    current_stage: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result_summary: Optional[dict]
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: datetime


class ExecutionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    execution_id: uuid.UUID
    stage_name: str
    status: StageStatus
    started_at: datetime
    ended_at: Optional[datetime]
    duration_ms: Optional[int]
    output_metadata: Optional[dict]
    error_message: Optional[str]


class ResearchRunAccepted(BaseModel):
    execution_id: uuid.UUID
    status: ExecutionStatus
    message: str
