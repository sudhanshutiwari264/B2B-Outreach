from app.integrations.tarqa_client import TarqaClient
from app.outreach.grounding import GROUNDING_RULES, build_strategy_context
from app.outreach.strategy_generator import OutreachStrategy
from app.schemas.draft import EmailDraftContent


async def generate_email_draft(tarqa: TarqaClient, strategy: OutreachStrategy) -> EmailDraftContent:
    messages = [
        {"role": "system", "content": GROUNDING_RULES},
        {
            "role": "user",
            "content": build_strategy_context(strategy)
            + """
Write a personalized cold outreach EMAIL using only the facts above. Return JSON with
these exact keys: subject, opening, contextual_observation, business_relevance,
value_proposition, call_to_action, body (the full assembled email text combining all the
other fields into one coherent, natural message, including a greeting and sign-off
placeholder like "- [Your name]").
Keep subject under 60 characters. Keep body under 180 words total.
""",
        },
    ]
    return await tarqa.generate_structured_output(messages, EmailDraftContent, max_tokens=900, temperature=0.5)
