import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import RelevanceTier, SignalType, VerificationStatus


class Signal(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "signals"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("research_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )

    signal_type: Mapped[SignalType] = mapped_column(
        SAEnum(SignalType, name="signal_type", native_enum=False, length=40), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    entity: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    evidence_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_reason: Mapped[str] = mapped_column(Text, nullable=False)

    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)

    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    business_impact_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evidence_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    relevance_tier: Mapped[Optional[RelevanceTier]] = mapped_column(
        SAEnum(RelevanceTier, name="relevance_tier", native_enum=False, length=10), nullable=True
    )

    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus, name="signal_verification_status", native_enum=False, length=20),
        default=VerificationStatus.NEEDS_REVIEW,
        nullable=False,
    )
    is_disputed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    execution: Mapped["Execution"] = relationship(back_populates="signals")
    source: Mapped["ResearchSource"] = relationship(back_populates="signals")
