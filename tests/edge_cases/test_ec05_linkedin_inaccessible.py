from sqlalchemy import select

from app.models.enums import ExtractionStatus, SourceType, VerificationStatus
from app.models.source import ResearchSource
from app.workflows.prospect_workflow import run_prospect_workflow
from tests.conftest import create_prospect_and_execution
from tests.fakes import FakeTarqaClient, FakeTavilyClient

PROSPECT = {"name": "Jordan Ashworth", "company": "Meridian Fintech", "designation": "Head of Platform"}

SEARCH_RESULTS = [
    {
        "url": "https://www.linkedin.com/in/jordan-ashworth-example",
        "title": "Jordan Ashworth",
        "snippet": "Jordan Ashworth - Head of Platform at Meridian Fintech, leading platform scaling efforts.",
        "query": "q", "category_hint": "linkedin_profile",
    },
    {
        "url": "https://www.fintechwire.example.com/meridian-platform-launch",
        "title": "Meridian Fintech launches new platform",
        "snippet": "Meridian Fintech today launched a new payments platform.",
        "query": "q", "category_hint": "company_news",
    },
]
EXTRACTED = [
    {
        "url": "https://www.fintechwire.example.com/meridian-platform-launch",
        "success": True, "title": "Meridian Fintech launches new platform",
        "text": "Meridian Fintech today launched a new payments platform. Head of Platform Jordan Ashworth said the launch reflects a year of engineering work.",
    }
]


async def test_linkedin_urls_are_never_crawled_but_research_continues(db_session):
    """EC-05: LinkedIn is marked restricted (snippet-only evidence) rather than attempting
    to bypass access controls, and other sources are still researched normally."""
    _, execution = await create_prospect_and_execution(db_session, PROSPECT)

    tavily = FakeTavilyClient(SEARCH_RESULTS, EXTRACTED)
    tarqa = FakeTarqaClient(entity=PROSPECT["name"], company=PROSPECT["company"])

    await run_prospect_workflow(db_session, execution.id, tavily=tavily, tarqa=tarqa)

    sources = (
        await db_session.execute(select(ResearchSource).where(ResearchSource.execution_id == execution.id))
    ).scalars().all()

    linkedin_sources = [s for s in sources if s.source_type == SourceType.LINKEDIN_PROFILE]
    assert linkedin_sources
    assert all(s.extraction_status == ExtractionStatus.RESTRICTED for s in linkedin_sources)
    assert all(s.verification_status == VerificationStatus.RESTRICTED for s in linkedin_sources)

    other_sources = [s for s in sources if s.source_type != SourceType.LINKEDIN_PROFILE]
    assert any(s.extraction_status == ExtractionStatus.SUCCESS for s in other_sources)
