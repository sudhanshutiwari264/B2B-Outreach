from app.integrations.schemas import NormalizedSearchResult
from app.integrations.tavily_client import TavilyClient
from app.research.query_runner import run_queries
from app.research.search_discovery import generate_company_queries
from app.schemas.prospect import ProspectCreate

_HINT_TO_METHOD = {"funding", "hiring"}


async def run_company_research(
    tavily: TavilyClient, prospect: ProspectCreate
) -> tuple[list[NormalizedSearchResult], list[str]]:
    """Research company announcements, funding, hiring, partnerships, growth, and
    publicly discussed challenges."""
    specs = generate_company_queries(prospect)

    async def search_fn(query: str, *, category_hint: str, max_results: int):
        if category_hint == "funding":
            return await tavily.search_funding(query, max_results=max_results)
        if category_hint == "hiring":
            return await tavily.search_company_hiring(query, max_results=max_results)
        if category_hint == "company_news":
            return await tavily.search_company_news(query, max_results=max_results)
        return await tavily.search_web(query, category_hint=category_hint, max_results=max_results)

    return await run_queries(search_fn, specs)
