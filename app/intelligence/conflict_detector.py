import re
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from typing import Optional

from app.models.enums import ConflictType, SignalType

DATE_MISMATCH_THRESHOLD_DAYS = 45
DATE_MISMATCH_OVERLAP_THRESHOLD = 0.55
DATE_MISMATCH_MIN_SHARED_WORDS = 3

# Only signal types that describe a single, datable occurrence are eligible for
# date-mismatch comparison. Recurring/ongoing categories like thought leadership or
# professional activity have many distinct instances about the same company and would
# otherwise generate false-positive conflicts just from shared vocabulary.
_DATE_MISMATCH_ELIGIBLE_TYPES = {
    SignalType.FUNDING,
    SignalType.LEADERSHIP_ANNOUNCEMENT,
    SignalType.JOB_CHANGE,
    SignalType.PARTNERSHIP,
}

_MONEY_RE = re.compile(
    r"[\$€£]\s?(\d+(?:\.\d+)?)\s?(million|billion|m|b|k|thousand)?", re.IGNORECASE
)
_TITLE_WORD = r"(?:Officer|President|Director|Manager|Head|Lead|VP|Vice President|CEO|CTO|CFO|COO)"
_TITLE_RE = re.compile(
    r"\b(?:as|named|appointed|promoted to|becomes?|is|was|serving as|serves as|,)\s+"
    r"(?:(?:its|the|a|new|current|incoming)\s+)*"
    rf"((?:[A-Z][a-zA-Z]*\s?){{1,5}}{_TITLE_WORD})",
)

_MONEY_MULTIPLIERS = {
    "k": 1_000, "thousand": 1_000,
    "m": 1_000_000, "million": 1_000_000,
    "b": 1_000_000_000, "billion": 1_000_000_000,
}


@dataclass
class SignalForConflictCheck:
    id: str
    signal_type: SignalType
    entity: str
    company: Optional[str]
    description: str
    evidence_excerpt: str
    published_at: Optional[datetime]


@dataclass
class DetectedConflict:
    conflict_type: ConflictType
    description: str
    signal_ids: list[str]
    conflicting_claims: list[dict]


def _extract_money_values(text: str) -> list[float]:
    values = []
    for amount, unit in _MONEY_RE.findall(text or ""):
        try:
            value = float(amount)
        except ValueError:
            continue
        multiplier = _MONEY_MULTIPLIERS.get((unit or "").lower(), 1)
        values.append(value * multiplier)
    return values


def _extract_titles(text: str) -> list[str]:
    return [m.strip() for m in _TITLE_RE.findall(text or "")]


def _detect_funding_amount_conflicts(signals: list[SignalForConflictCheck]) -> list[DetectedConflict]:
    funding_signals = [s for s in signals if s.signal_type == SignalType.FUNDING]
    by_company: dict[str, list[tuple[SignalForConflictCheck, float]]] = {}
    for s in funding_signals:
        for value in _extract_money_values(s.description + " " + s.evidence_excerpt):
            by_company.setdefault((s.company or "").lower(), []).append((s, value))

    conflicts = []
    for company, entries in by_company.items():
        distinct_values = {round(v, 2) for _, v in entries}
        if len(distinct_values) > 1:
            conflicts.append(
                DetectedConflict(
                    conflict_type=ConflictType.FUNDING_AMOUNT,
                    description=f"Conflicting funding amounts reported for {company or 'company'}: {sorted(distinct_values)}",
                    signal_ids=[s.id for s, _ in entries],
                    conflicting_claims=[
                        {"signal_id": s.id, "amount": v} for s, v in entries
                    ],
                )
            )
    return conflicts


def _detect_job_title_conflicts(signals: list[SignalForConflictCheck]) -> list[DetectedConflict]:
    relevant = [
        s for s in signals
        if s.signal_type in (SignalType.JOB_CHANGE, SignalType.LEADERSHIP_ANNOUNCEMENT)
    ]
    by_entity: dict[str, list[tuple[SignalForConflictCheck, str]]] = {}
    for s in relevant:
        for title in _extract_titles(s.description + " " + s.evidence_excerpt):
            by_entity.setdefault(s.entity.lower(), []).append((s, title.lower()))

    conflicts = []
    for entity, entries in by_entity.items():
        distinct_titles = {t for _, t in entries}
        if len(distinct_titles) > 1:
            conflicts.append(
                DetectedConflict(
                    conflict_type=ConflictType.JOB_TITLE,
                    description=f"Conflicting job titles reported for {entity}: {sorted(distinct_titles)}",
                    signal_ids=[s.id for s, _ in entries],
                    conflicting_claims=[{"signal_id": s.id, "title": t} for s, t in entries],
                )
            )
    return conflicts


def _detect_date_mismatches(signals: list[SignalForConflictCheck]) -> list[DetectedConflict]:
    conflicts = []
    by_type_company: dict[tuple, list[SignalForConflictCheck]] = {}
    for s in signals:
        if s.published_at is None or s.signal_type not in _DATE_MISMATCH_ELIGIBLE_TYPES:
            continue
        key = (s.signal_type, (s.company or "").lower())
        by_type_company.setdefault(key, []).append(s)

    for (signal_type, company), group in by_type_company.items():
        if len(group) < 2:
            continue
        for a, b in combinations(group, 2):
            delta_days = abs((a.published_at - b.published_at).days)
            if delta_days > DATE_MISMATCH_THRESHOLD_DAYS and _descriptions_overlap(a.description, b.description):
                conflicts.append(
                    DetectedConflict(
                        conflict_type=ConflictType.DATE_MISMATCH,
                        description=(
                            f"Sources disagree on the date of a {signal_type.value} event for "
                            f"{company or 'company'} (difference of {delta_days} days)"
                        ),
                        signal_ids=[a.id, b.id],
                        conflicting_claims=[
                            {"signal_id": a.id, "published_at": a.published_at.isoformat()},
                            {"signal_id": b.id, "published_at": b.published_at.isoformat()},
                        ],
                    )
                )
    return conflicts


def _descriptions_overlap(
    a: str, b: str, threshold: float = DATE_MISMATCH_OVERLAP_THRESHOLD
) -> bool:
    """Jaccard similarity over significant words - deliberately strict, since this gates
    whether two signals are treated as describing the *same* real-world event with
    disputed dates, rather than two unrelated events that merely share vocabulary."""
    wa = {w.lower().strip(".,:;\"'") for w in a.split() if len(w) > 4}
    wb = {w.lower().strip(".,:;\"'") for w in b.split() if len(w) > 4}
    if not wa or not wb:
        return False
    shared = wa & wb
    if len(shared) < DATE_MISMATCH_MIN_SHARED_WORDS:
        return False
    overlap = len(shared) / len(wa | wb)
    return overlap >= threshold


def _detect_identity_ambiguity(
    signals: list[SignalForConflictCheck], prospect_name: str, prospect_company: str
) -> list[DetectedConflict]:
    conflicts = []
    suspect = [
        s for s in signals
        if s.company and s.company.strip().lower() != prospect_company.strip().lower()
    ]
    if suspect:
        conflicts.append(
            DetectedConflict(
                conflict_type=ConflictType.IDENTITY_AMBIGUITY,
                description=(
                    f"{len(suspect)} signal(s) reference a company other than "
                    f"'{prospect_company}' for an entity matching '{prospect_name}' - "
                    "possible name collision with a different person."
                ),
                signal_ids=[s.id for s in suspect],
                conflicting_claims=[{"signal_id": s.id, "company": s.company} for s in suspect],
            )
        )
    return conflicts


def detect_conflicts(
    signals: list[SignalForConflictCheck], *, prospect_name: str, prospect_company: str
) -> list[DetectedConflict]:
    """Deterministic conflict detection across already-extracted signals.

    Never lets the LLM arbitrate between conflicting claims - all comparisons here are
    plain Python logic over the structured signal fields. Source records are untouched;
    this only flags which signals are disputed so the workflow can exclude them from
    outreach and route the execution to human review (section 11).
    """
    return (
        _detect_funding_amount_conflicts(signals)
        + _detect_job_title_conflicts(signals)
        + _detect_date_mismatches(signals)
        + _detect_identity_ambiguity(signals, prospect_name, prospect_company)
    )
