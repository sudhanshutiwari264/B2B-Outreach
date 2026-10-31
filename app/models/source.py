import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin, utcnow
from app.models.enums import EvidenceType, ExtractionStatus, SourceType, VerificationStatus


class ResearchSource(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "research_sources"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    normalized_url: Mapped[str] = mapped_column(String(2000), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(300), nullable=True, index=True)
    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, name="source_type", native_enum=False, length=40),
        default=SourceType.OTHER,
        nullable=False,
    )
    evidence_type: Mapped[EvidenceType] = mapped_column(
        SAEnum(EvidenceType, name="evidence_type", native_enum=False, length=30),
        default=EvidenceType.SEARCH_SNIPPET,
        nullable=False,
    )

    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    extracted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        SAEnum(ExtractionStatus, name="extraction_status", native_enum=False, length=20),
        default=ExtractionStatus.PENDING,
        nullable=False,
    )
    extraction_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus, name="source_verification_status", native_enum=False, length=20),
        default=VerificationStatus.PENDING,
        nullable=False,
    )

    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    execution: Mapped["Execution"] = relationship(back_populates="sources")
    signals: Mapped[list["Signal"]] = relationship(back_populates="source")
