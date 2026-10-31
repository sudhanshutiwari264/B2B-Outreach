import uuid
from typing import Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import OutreachChannel


class Prospect(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "prospects"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    designation: Mapped[str] = mapped_column(String(200), nullable=False)

    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    company_website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    outreach_channel: Mapped[OutreachChannel] = mapped_column(
        SAEnum(OutreachChannel, name="outreach_channel", native_enum=False, length=20),
        default=OutreachChannel.EMAIL,
        nullable=False,
    )
    product_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    executions: Mapped[list["Execution"]] = relationship(
        back_populates="prospect", cascade="all, delete-orphan"
    )
