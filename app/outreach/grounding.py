from app.outreach.strategy_generator import OutreachStrategy

GROUNDING_RULES = """You are drafting a personalized B2B outreach message. You will be given a verified
strategy object containing exactly the facts you are allowed to reference - a single
evidence-backed signal about the prospect/company, and a short description of our
product/offering.

Hard rules:
- Only state facts that appear in the provided strategy/signal/evidence. Never invent
  funding amounts, dates, achievements, titles, or company details not given to you.
- Do not fabricate a personal relationship with the prospect.
- Avoid generic AI-sounding openers ("I hope this email finds you well", "I came across
  your profile and was impressed").
- Avoid excessive flattery and avoid exaggerated claims about our product.
- Keep the message natural, concise, and specific to the one evidence-backed signal given.
- Respond with ONLY a single JSON object matching the required schema - no markdown
  fences, no commentary.
"""


def build_strategy_context(strategy: OutreachStrategy) -> str:
    return f"""PROSPECT: {strategy.prospect_name}, {strategy.prospect_role}
COMPANY CONTEXT: {strategy.company_context}
COMMUNICATION ANGLE: {strategy.communication_angle}
VERIFIED SIGNAL: {strategy.signal_description}
WHY IT MATTERS: {strategy.signal_relevance_reason}
SUPPORTING EVIDENCE (verbatim excerpt, source: {strategy.source_url}):
"{strategy.evidence_excerpt}"
OUR PRODUCT/OFFERING CONTEXT: {strategy.value_proposition_hint or "No product context was provided - keep the value proposition generic and brief, or omit it."}
"""
