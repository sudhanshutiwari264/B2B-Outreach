from datetime import datetime, timezone

from app.intelligence.conflict_detector import SignalForConflictCheck, detect_conflicts
from app.models.enums import ConflictType, SignalType


def _sig(id_, signal_type, entity="Priya Chandrasekaran", company="Fieldglass Robotics", description="", excerpt="", published_at=None):
    return SignalForConflictCheck(
        id=id_, signal_type=signal_type, entity=entity, company=company,
        description=description, evidence_excerpt=excerpt, published_at=published_at,
    )


def test_detect_job_title_conflicts():
    """EC-02: two sources give different titles for the same person."""
    signals = [
        _sig("s1", SignalType.JOB_CHANGE, description="Priya was named as Chief Operating Officer",
             excerpt="named as Chief Operating Officer effective immediately"),
        _sig("s2", SignalType.LEADERSHIP_ANNOUNCEMENT, description="Priya is Chief Strategy Officer",
             excerpt="Priya Chandrasekaran, Chief Strategy Officer at Fieldglass Robotics"),
    ]
    conflicts = detect_conflicts(signals, prospect_name="Priya Chandrasekaran", prospect_company="Fieldglass Robotics")
    job_title_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.JOB_TITLE]
    assert len(job_title_conflicts) == 1
    assert set(job_title_conflicts[0].signal_ids) == {"s1", "s2"}


def test_detect_funding_amount_conflicts():
    signals = [
        _sig("s1", SignalType.FUNDING, entity="Acme", company="Acme Corp",
             description="Acme raised $10 million in funding", excerpt="raised $10 million"),
        _sig("s2", SignalType.FUNDING, entity="Acme", company="Acme Corp",
             description="Acme raised $25 million in funding", excerpt="raised $25 million"),
    ]
    conflicts = detect_conflicts(signals, prospect_name="Jane Doe", prospect_company="Acme Corp")
    funding_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.FUNDING_AMOUNT]
    assert len(funding_conflicts) == 1


def test_detect_date_mismatch_for_same_event():
    d1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    d2 = datetime(2026, 6, 1, tzinfo=timezone.utc)
    signals = [
        _sig("s1", SignalType.FUNDING, entity="Acme", company="Acme Corp",
             description="Acme Corp closed its Series B funding round", published_at=d1),
        _sig("s2", SignalType.FUNDING, entity="Acme", company="Acme Corp",
             description="Acme Corp closed its Series B funding round", published_at=d2),
    ]
    conflicts = detect_conflicts(signals, prospect_name="Jane Doe", prospect_company="Acme Corp")
    date_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.DATE_MISMATCH]
    assert len(date_conflicts) == 1


def test_detect_identity_ambiguity_when_company_differs():
    """EC-11: a signal about someone with the same name but a different company should be
    flagged, not silently merged into this prospect's evidence."""
    signals = [
        _sig("s1", SignalType.PROFESSIONAL_ACTIVITY, entity="Jane Doe", company="A Totally Different Company",
             description="Jane Doe spoke at a conference"),
    ]
    conflicts = detect_conflicts(signals, prospect_name="Jane Doe", prospect_company="Acme Corp")
    identity_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.IDENTITY_AMBIGUITY]
    assert len(identity_conflicts) == 1
    assert "s1" in identity_conflicts[0].signal_ids


def test_no_conflicts_for_consistent_signals():
    signals = [
        _sig("s1", SignalType.FUNDING, entity="Acme", company="Acme Corp", description="Acme raised $10 million"),
    ]
    conflicts = detect_conflicts(signals, prospect_name="Jane Doe", prospect_company="Acme Corp")
    assert conflicts == []
