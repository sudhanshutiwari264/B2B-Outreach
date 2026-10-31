import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import RelevanceTier, SignalType, VerificationStatus


class ExtractedSignalLLM(BaseModel):
    """Strict schema the LLM must conform to when extracting a signal from a single source.

    The model is only ever shown one source's content at a time, so it cannot know the
    source's database id - that is attached by our code after validation, not by the LLM.
    """

    model_config = ConfigDict(extra="forbid")

    signal_type: SignalType
    description: str = Field(..., min_length=5, max_length=1000)
    entity: str = Field(..., min_length=1, max_length=200)
    company: Optional[str] = Field(default=None, max_length=200)
    published_at: Optional[str] = Field(
        default=None, description="ISO-8601 date/datetime string if determinable from the source, else null"
    )
    evidence_excerpt: str = Field(..., min_length=5, max_length=2000)
    relevance_reason: str = Field(..., min_length=5, max_length=1000)
    confidence_score: int = Field(..., ge=0, le=100)

    @field_validator("published_at")
    @classmethod
    def validate_published_at(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "" or v.lower() == "null":
            return None
        return v


class SignalExtractionLLMResponse(BaseModel):
    """Top level structured response requested from the LLM for one source."""

    model_config = ConfigDict(extra="forbid")

    signals: list[ExtractedSignalLLM] = Field(default_factory=list)
    insufficient_evidence: bool = False
    notes: Optional[str] = None


class SignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    execution_id: uuid.UUID
    source_id: uuid.UUID
    signal_type: SignalType
    description: str
    entity: str
    company: Optional[str]
    published_at: Optional[datetime]
    evidence_excerpt: str
    relevance_reason: str
    confidence_score: int
    relevance_score: Optional[float]
    business_impact_score: Optional[float]
    recency_score: Optional[float]
    evidence_quality_score: Optional[float]
    final_score: Optional[float]
    relevance_tier: Optional[RelevanceTier]
    verification_status: VerificationStatus
    is_disputed: bool
