from app.models.enums import OutreachChannel, SignalType
from app.outreach.outreach_validator import validate_draft
from app.outreach.strategy_generator import OutreachStrategy

STRATEGY = OutreachStrategy(
    prospect_name="Jane Doe",
    prospect_role="VP of Engineering",
    company_context="Acme Corp just raised a Series B",
    signal_id="sig-1",
    signal_type=SignalType.FUNDING,
    signal_description="Acme Corp raised a $28M Series B to expand engineering",
    signal_relevance_reason="Funding usually means headcount and tooling growth",
    communication_angle="Congratulate on the funding milestone",
    value_proposition_hint="workflow automation platform",
    evidence_excerpt="Acme Corp raised a $28 million Series B to expand its engineering team",
    source_url="https://example.com/acme-series-b",
    source_id="src-1",
)


def test_validate_draft_passes_a_well_formed_message():
    body = (
        "Hi Jane, congrats on Acme Corp's $28 million Series B and the engineering team "
        "expansion that comes with it. We help teams like yours automate workflow "
        "bottlenecks as they scale. Would you be open to a quick call next week?"
    )
    report = validate_draft(body, STRATEGY, OutreachChannel.EMAIL)
    assert report.passed, report.issues


def test_validate_draft_flags_generic_ai_opener():
    body = "I hope this email finds you well. We would love to chat about our product. Let me know!"
    report = validate_draft(body, STRATEGY, OutreachChannel.EMAIL)
    assert report.checks["no_generic_ai_opener"] is False


def test_validate_draft_flags_fabricated_relationship():
    body = "As we discussed last time, I wanted to follow up about Acme Corp's Series B. Let me know if you're open to chat."
    report = validate_draft(body, STRATEGY, OutreachChannel.EMAIL)
    assert report.checks["no_fabricated_relationship"] is False


def test_validate_draft_flags_missing_call_to_action():
    body = (
        "Hi Jane, congrats on Acme Corp's $28 million Series B. We help teams scale their "
        "engineering workflows as they grow headcount quickly after raises like this one."
    )
    report = validate_draft(body, STRATEGY, OutreachChannel.EMAIL)
    assert report.checks["has_call_to_action"] is False


def test_validate_draft_flags_too_short_message():
    report = validate_draft("Hi Jane, congrats!", STRATEGY, OutreachChannel.EMAIL)
    assert report.checks["length_within_bounds"] is False


def test_validate_draft_flags_ungrounded_message():
    body = (
        "Hi Jane, I saw your company just hired 500 new salespeople and wanted to reach out "
        "about our product. Would you like to connect sometime?"
    )
    report = validate_draft(body, STRATEGY, OutreachChannel.EMAIL)
    assert report.checks["references_verified_signal"] is False
