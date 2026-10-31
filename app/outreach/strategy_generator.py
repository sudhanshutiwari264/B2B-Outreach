from dataclasses import dataclass
from typing import Optional

from app.models.enums import SignalType

_ANGLE_BY_SIGNAL_TYPE: dict[SignalType, str] = {
    SignalType.FUNDING: "Congratulate on the funding milestone and connect it to scaling needs",
    SignalType.JOB_CHANGE: "Acknowledge the new role/transition and its likely early priorities",
    SignalType.LEADERSHIP_ANNOUNCEMENT: "Acknowledge the leadership update and its strategic implications",
    SignalType.COMPANY_GROWTH: "Reference the company's growth trajectory",
    SignalType.HIRING: "Reference the hiring push and the scaling challenges that come with it",
    SignalType.PRODUCT_DEVELOPMENT: "Reference the product development and its relevance to their roadmap",
    SignalType.BUSINESS_CHALLENGE: "Acknowledge the challenge thoughtfully, without being presumptuous",
    SignalType.THOUGHT_LEADERSHIP: "Reference their publicly shared perspective",
    SignalType.PARTNERSHIP: "Reference the partnership and its strategic direction",
    SignalType.PUBLIC_SPEAKING: "Reference their recent talk or public appearance",
    SignalType.INDUSTRY_DEVELOPMENT: "Connect the industry development to their likely priorities",
    SignalType.PROFESSIONAL_ACTIVITY: "Reference their recent professional activity",
}


@dataclass
class OutreachStrategy:
    prospect_name: str
    prospect_role: str
    company_context: str
    signal_id: str
    signal_type: SignalType
    signal_description: str
    signal_relevance_reason: str
    communication_angle: str
    value_proposition_hint: Optional[str]
    evidence_excerpt: str
    source_url: str
    source_id: str


def generate_strategy(
    *,
    prospect_name: str,
    prospect_role: str,
    company: str,
    product_context: Optional[str],
    signal_id: str,
    signal_type: SignalType,
    signal_description: str,
    signal_relevance_reason: str,
    evidence_excerpt: str,
    source_url: str,
    source_id: str,
) -> OutreachStrategy:
    """Deterministic strategy assembly (section 12): picks a communication angle from a
    fixed mapping keyed on the verified signal's type, rather than letting the LLM invent
    an angle untethered from evidence. The actual sentence-level writing happens later in
    email_generator/linkedin_generator, constrained to this strategy's facts only.
    """
    angle = _ANGLE_BY_SIGNAL_TYPE.get(signal_type, "Reference their recent public activity")

    return OutreachStrategy(
        prospect_name=prospect_name,
        prospect_role=prospect_role,
        company_context=f"{company} - context derived from: {signal_description}",
        signal_id=signal_id,
        signal_type=signal_type,
        signal_description=signal_description,
        signal_relevance_reason=signal_relevance_reason,
        communication_angle=angle,
        value_proposition_hint=product_context,
        evidence_excerpt=evidence_excerpt,
        source_url=source_url,
        source_id=source_id,
    )
