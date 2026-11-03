import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DraftStatus, OutreachChannel


class EmailDraftContent(BaseModel):
    subject: str = Field(..., min_length=3, max_length=300)
    opening: str
    contextual_observation: str
    business_relevance: str
    value_proposition: str
    call_to_action: str
    body: str


class LinkedInDraftContent(BaseModel):
    opening: str
    professional_observation: str
    conversational_context: str
    call_to_action: str
    body: str


class DraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    execution_id: uuid.UUID
    channel: OutreachChannel
    subject: Optional[str]
    body: str
    edited_subject: Optional[str]
    edited_body: Optional[str]
    used_signal_ids: list
    used_source_ids: list
    validation_report: Optional[dict]
    status: DraftStatus
    reviewer_notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class DraftEditRequest(BaseModel):
    subject: Optional[str] = Field(default=None, max_length=300)
    body: str = Field(..., min_length=10, max_length=8000)
    reviewer_notes: Optional[str] = Field(default=None, max_length=2000)


class DraftRejectRequest(BaseModel):
    reviewer_notes: Optional[str] = Field(default=None, max_length=2000)
