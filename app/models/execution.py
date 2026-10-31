import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import ExecutionStatus


class Execution(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "executions"

    prospect_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ExecutionStatus] = mapped_column(
        SAEnum(ExecutionStatus, name="execution_status", native_enum=False, length=30),
        default=ExecutionStatus.QUEUED,
        nullable=False,
        index=True,
    )
    current_stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, unique=True, index=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    result_summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    prospect: Mapped["Prospect"] = relationship(back_populates="executions")
    sources: Mapped[list["ResearchSource"]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )
    signals: Mapped[list["Signal"]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )
    conflicts: Mapped[list["SignalConflict"]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )
    drafts: Mapped[list["OutreachDraft"]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )
    logs: Mapped[list["ExecutionLog"]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )
