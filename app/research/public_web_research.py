from app.integrations.schemas import NormalizedSearchResult
from app.integrations.tavily_client import TavilyClient
from app.research.query_runner import run_queries
from app.research.search_discovery import generate_professional_queries
from app.schemas.prospect import ProspectCreate


async def run_professional_research(
    tavily: TavilyClient, prospect: ProspectCreate
) -> tuple[list[NormalizedSearchResult], list[str]]:
    """Research interviews, podcasts, conference appearances, and published opinions."""
    specs = generate_professional_queries(prospect)

    async def search_fn(query: str, *, category_hint: str, max_results: int):
        return await tavily.search_web(query, category_hint=category_hint, max_results=max_results)

    return await run_queries(search_fn, specs)
