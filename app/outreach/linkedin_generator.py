from app.integrations.tarqa_client import TarqaClient
from app.outreach.grounding import GROUNDING_RULES, build_strategy_context
from app.outreach.strategy_generator import OutreachStrategy
from app.schemas.draft import LinkedInDraftContent


async def generate_linkedin_draft(
    tarqa: TarqaClient, strategy: OutreachStrategy
) -> LinkedInDraftContent:
    messages = [
        {"role": "system", "content": GROUNDING_RULES},
        {
            "role": "user",
            "content": build_strategy_context(strategy)
            + """
Write a personalized cold outreach LINKEDIN message using only the facts above. Return
JSON with these exact keys: opening, professional_observation, conversational_context,
call_to_action, body (the full assembled message combining the other fields into one
short, natural, conversational note - no greeting formalities like "Dear", no sign-off
block, this is a LinkedIn DM).
Keep body under 80 words total.
""",
        },
    ]
    return await tarqa.generate_structured_output(
        messages, LinkedInDraftContent, max_tokens=600, temperature=0.5
    )
