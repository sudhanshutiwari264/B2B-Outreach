import re
from dataclasses import dataclass, field

from app.models.enums import OutreachChannel
from app.outreach.strategy_generator import OutreachStrategy

MAX_EMAIL_WORDS = 200
MAX_LINKEDIN_WORDS = 90
MIN_WORDS = 15

_GENERIC_OPENERS = [
    "i hope this email finds you well",
    "i hope this message finds you well",
    "i came across your profile",
    "as an ai",
    "i wanted to reach out",
]

_FLATTERY_PHRASES = [
    "truly inspiring",
    "amazing work you",
    "incredibly impressed",
    "biggest fan",
]

_FALSE_RELATIONSHIP_PHRASES = [
    "as we discussed",
    "as we spoke about",
    "great catching up",
    "my friend",
    "we met at",
]

_UNFILLED_PLACEHOLDER_RE = re.compile(r"\[[a-zA-Z _]{2,30}\]")

_WEAK_CTA_MARKERS = ["let me know", "would you be open", "worth a quick", "interested in", "?"]


@dataclass
class OutreachValidationReport:
    passed: bool
    issues: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)


def _word_count(text: str) -> int:
    return len(text.split())


def _repetitiveness_ratio(text: str) -> float:
    words = [w.lower().strip(".,!?") for w in text.split() if len(w) > 2]
    if not words:
        return 0.0
    return 1 - (len(set(words)) / len(words))


def validate_draft(
    body: str, strategy: OutreachStrategy, channel: OutreachChannel
) -> OutreachValidationReport:
    """Deterministic quality gate for a generated draft (section 13):
    factual grounding, unsupported-statement smells, personalization quality, length,
    repetitiveness, and call-to-action presence. This runs after generation and before a
    draft is exposed for human review - failures are recorded, not silently dropped.
    """
    issues: list[str] = []
    checks: dict[str, bool] = {}
    lowered = body.lower()

    word_count = _word_count(body)
    max_words = MAX_EMAIL_WORDS if channel == OutreachChannel.EMAIL else MAX_LINKEDIN_WORDS
    length_ok = MIN_WORDS <= word_count <= max_words
    checks["length_within_bounds"] = length_ok
    if not length_ok:
        issues.append(f"Word count {word_count} is outside the expected range ({MIN_WORDS}-{max_words})")

    generic_hits = [p for p in _GENERIC_OPENERS if p in lowered]
    checks["no_generic_ai_opener"] = not generic_hits
    if generic_hits:
        issues.append(f"Contains generic AI-style opener(s): {generic_hits}")

    flattery_hits = [p for p in _FLATTERY_PHRASES if p in lowered]
    checks["no_excessive_flattery"] = not flattery_hits
    if flattery_hits:
        issues.append(f"Contains excessive flattery: {flattery_hits}")

    relationship_hits = [p for p in _FALSE_RELATIONSHIP_PHRASES if p in lowered]
    checks["no_fabricated_relationship"] = not relationship_hits
    if relationship_hits:
        issues.append(f"Implies a personal relationship that was never established: {relationship_hits}")

    placeholders = _UNFILLED_PLACEHOLDER_RE.findall(body)
    unfilled = [p for p in placeholders if p.lower() not in ("[your name]",)]
    checks["no_unfilled_placeholders"] = not unfilled
    if unfilled:
        issues.append(f"Contains unfilled placeholder(s): {unfilled}")

    repetitiveness = _repetitiveness_ratio(body)
    repetitiveness_ok = repetitiveness < 0.6
    checks["not_repetitive"] = repetitiveness_ok
    if not repetitiveness_ok:
        issues.append(f"Message is highly repetitive (ratio={repetitiveness:.2f})")

    has_cta = any(marker in lowered for marker in _WEAK_CTA_MARKERS)
    checks["has_call_to_action"] = has_cta
    if not has_cta:
        issues.append("No clear call-to-action detected")

    evidence_keywords = [
        w.lower().strip(".,:;\"'") for w in strategy.evidence_excerpt.split() if len(w) > 5
    ]
    grounding_hits = sum(1 for w in set(evidence_keywords) if w in lowered)
    grounded = len(evidence_keywords) == 0 or grounding_hits >= 1
    checks["references_verified_signal"] = grounded
    if not grounded:
        issues.append("Draft does not appear to reference the verified signal's evidence")

    return OutreachValidationReport(passed=not issues, issues=issues, checks=checks)
