from sqlalchemy import select

from app.models.conflict import SignalConflict
from app.models.enums import ConflictType
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution
from tests.fakes import FakeTarqaClient, FakeTavilyClient

PROSPECT = {"name": "Morgan Reyes", "company": "Delacroix Materials", "designation": "CFO"}

SEARCH_RESULTS = [
    {
        "url": "https://www.industrynews.example.com/delacroix-expansion",
        "title": "Delacroix Materials expands production",
        "snippet": "Delacroix Materials announced a production expansion, with CFO Morgan Reyes noting strong demand.",
        "query": "q", "category_hint": "company_news",
    }
]
EXTRACTED = [
    {
        "url": "https://www.industrynews.example.com/delacroix-expansion",
        "success": True, "title": "Delacroix Materials expands production",
        "text": "Delacroix Materials announced a production expansion, with CFO Morgan Reyes noting strong demand.",
    }
]


async def test_same_name_different_company_is_flagged_not_merged(db_session):
    """EC-11: a signal's reported company doesn't match the prospect's actual company -
    likely a different person with the same name. The system must flag this rather than
    silently attributing someone else's facts to our prospect."""
    _, execution = await create_prospect_and_execution(db_session, PROSPECT)

    tavily = FakeTavilyClient(SEARCH_RESULTS, EXTRACTED)
    # Simulate the LLM (correctly) extracting a company name that doesn't match the
    # prospect's actual company - a name-collision scenario.
    tarqa = FakeTarqaClient(entity=PROSPECT["name"], company="A Totally Unrelated Company")

    await run_prospect_workflow(db_session, execution.id, tavily=tavily, tarqa=tarqa)

    conflicts = (
        await db_session.execute(select(SignalConflict).where(SignalConflict.execution_id == execution.id))
    ).scalars().all()
    assert any(c.conflict_type == ConflictType.IDENTITY_AMBIGUITY for c in conflicts)
