import uuid
from typing import Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import DraftStatus, OutreachChannel


class OutreachDraft(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "outreach_drafts"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    channel: Mapped[OutreachChannel] = mapped_column(
        SAEnum(OutreachChannel, name="draft_channel", native_enum=False, length=20), nullable=False
    )
    subject: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    edited_subject: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    edited_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    used_signal_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    used_source_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    validation_report: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    status: Mapped[DraftStatus] = mapped_column(
        SAEnum(DraftStatus, name="draft_status", native_enum=False, length=30),
        default=DraftStatus.DRAFT_GENERATED,
        nullable=False,
    )
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    execution: Mapped["Execution"] = relationship(back_populates="drafts")
