import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import EvidenceType, ExtractionStatus, SourceType, VerificationStatus


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    execution_id: uuid.UUID
    url: str
    normalized_url: str
    title: Optional[str]
    domain: Optional[str]
    source_type: SourceType
    evidence_type: EvidenceType
    content: Optional[str]
    content_hash: Optional[str]
    published_at: Optional[datetime]
    discovered_at: datetime
    extracted_at: Optional[datetime]
    extraction_status: ExtractionStatus
    extraction_error: Optional[str]
    verification_status: VerificationStatus
