from sqlalchemy import select

from app.intelligence.recency_scorer import score_recency
from app.models.signal import Signal
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution, get_sample_fixture, get_sample_prospect
from tests.fakes import FakeTarqaClient, FakeTavilyClient


async def test_outdated_signal_gets_discounted_recency_score(db_session):
    """EC-04: a signal whose only evidence is multiple years old must be scored with the
    lowest recency bucket, not treated as if it were current."""
    prospect_dict = get_sample_prospect("outdated_news_only")
    fixture = get_sample_fixture("outdated_news_only")

    _, execution = await create_prospect_and_execution(db_session, prospect_dict)

    tavily = FakeTavilyClient(fixture["search_results"], fixture["extracted_contents"])
    tarqa = FakeTarqaClient(entity=prospect_dict["name"], company=prospect_dict["company"])

    await run_prospect_workflow(db_session, execution.id, tavily=tavily, tarqa=tarqa)

    signals = (
        await db_session.execute(select(Signal).where(Signal.execution_id == execution.id))
    ).scalars().all()
    assert signals, "expected at least one signal to be extracted from the outdated source"

    for s in signals:
        assert s.recency_score == score_recency(None) or s.recency_score <= 35.0
