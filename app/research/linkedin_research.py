from app.integrations.schemas import NormalizedSearchResult
from app.integrations.tavily_client import TavilyClient
from app.research.query_runner import run_queries
from app.research.search_discovery import generate_linkedin_queries
from app.schemas.prospect import ProspectCreate


async def run_linkedin_research(
    tavily: TavilyClient, prospect: ProspectCreate
) -> tuple[list[NormalizedSearchResult], list[str]]:
    """Discover publicly indexed LinkedIn profile/post evidence via Tavily search only.

    This never authenticates to LinkedIn, bypasses no access controls, and never scrapes
    logged-in pages - it only surfaces what Tavily's public web index already contains
    (search snippets, not full page content). See EC-05 for the inaccessible-page path.
    """
    specs = generate_linkedin_queries(prospect)

    async def search_fn(query: str, *, category_hint: str, max_results: int):
        if category_hint == "linkedin_post":
            return await tavily.discover_linkedin_posts(query, max_results=max_results)
        if category_hint == "linkedin_profile":
            return await tavily.discover_linkedin_profile(query, max_results=max_results)
        return await tavily.search_web(query, category_hint=category_hint, max_results=max_results)

    return await run_queries(search_fn, specs)
