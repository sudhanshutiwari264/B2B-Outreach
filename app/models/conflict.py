import uuid
from typing import Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import ConflictResolutionStatus, ConflictType


class SignalConflict(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "signal_conflicts"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    conflict_type: Mapped[ConflictType] = mapped_column(
        SAEnum(ConflictType, name="conflict_type", native_enum=False, length=30), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    signal_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    conflicting_claims: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    resolution_status: Mapped[ConflictResolutionStatus] = mapped_column(
        SAEnum(ConflictResolutionStatus, name="conflict_resolution_status", native_enum=False, length=30),
        default=ConflictResolutionStatus.UNRESOLVED,
        nullable=False,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    execution: Mapped["Execution"] = relationship(back_populates="conflicts")
