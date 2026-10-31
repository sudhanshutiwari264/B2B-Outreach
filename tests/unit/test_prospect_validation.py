import pytest
from pydantic import ValidationError

from app.schemas.prospect import ProspectCreate
from app.validation.prospect_validator import validate_prospect_identity


def test_prospect_create_requires_core_fields():
    with pytest.raises(ValidationError):
        ProspectCreate(name="Jane Doe", designation="VP")  # missing company


def test_prospect_create_rejects_non_linkedin_url():
    with pytest.raises(ValidationError):
        ProspectCreate(
            name="Jane Doe", company="Acme", designation="VP",
            linkedin_url="https://facebook.com/jane.doe",
        )


def test_prospect_create_rejects_malformed_website():
    with pytest.raises(ValidationError):
        ProspectCreate(name="Jane Doe", company="Acme", designation="VP", company_website="not-a-url")


def test_prospect_create_accepts_valid_payload():
    p = ProspectCreate(
        name="Jane Doe", company="Acme Corp", designation="VP of Engineering",
        linkedin_url="https://www.linkedin.com/in/janedoe",
        company_website="https://acme.example.com",
    )
    assert p.outreach_channel.value == "email"


def test_validate_prospect_identity_rejects_single_word_name():
    """EC-03 / EC-11: a bare first name cannot be uniquely identified via public search."""
    p = ProspectCreate(name="Alex", company="Initech", designation="Manager")
    result = validate_prospect_identity(p)
    assert result.is_identifiable is False
    assert "name" in result.missing_fields


def test_validate_prospect_identity_rejects_generic_company():
    p = ProspectCreate(name="Jane Doe", company="Inc", designation="Manager")
    result = validate_prospect_identity(p)
    assert result.is_identifiable is False


def test_validate_prospect_identity_accepts_well_formed_prospect():
    p = ProspectCreate(name="Jane Doe", company="Acme Corp", designation="VP of Engineering")
    result = validate_prospect_identity(p)
    assert result.is_identifiable is True
    assert result.reason is None
