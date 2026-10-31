import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import OutreachChannel


class ProspectCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=2, max_length=200)
    company: str = Field(..., min_length=2, max_length=200)
    designation: str = Field(..., min_length=2, max_length=200)

    linkedin_url: Optional[str] = Field(default=None, max_length=500)
    company_website: Optional[str] = Field(default=None, max_length=500)
    industry: Optional[str] = Field(default=None, max_length=200)
    outreach_channel: OutreachChannel = OutreachChannel.EMAIL
    product_context: Optional[str] = Field(default=None, max_length=5000)

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not v.startswith(("http://", "https://")):
            raise ValueError("linkedin_url must be a valid http(s) URL")
        if "linkedin.com" not in v.lower():
            raise ValueError("linkedin_url must point to a linkedin.com domain")
        return v

    @field_validator("company_website")
    @classmethod
    def validate_company_website(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not v.startswith(("http://", "https://")):
            raise ValueError("company_website must be a valid http(s) URL")
        return v

    @field_validator("name", "company", "designation")
    @classmethod
    def validate_non_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("field cannot be blank")
        return v.strip()


class ProspectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    company: str
    designation: str
    linkedin_url: Optional[str]
    company_website: Optional[str]
    industry: Optional[str]
    outreach_channel: OutreachChannel
    product_context: Optional[str]
    created_at: datetime
    updated_at: datetime


class ProspectIdentityCheck(BaseModel):
    """Result of ambiguity/identity validation performed before research starts."""

    is_identifiable: bool
    reason: Optional[str] = None
    missing_fields: list[str] = Field(default_factory=list)
