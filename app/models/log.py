import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import StageStatus


class ExecutionLog(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "execution_logs"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    stage_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[StageStatus] = mapped_column(
        SAEnum(StageStatus, name="stage_status", native_enum=False, length=20), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    output_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    execution: Mapped["Execution"] = relationship(back_populates="logs")
