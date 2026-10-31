from collections.abc import Awaitable, Callable

from app.integrations.schemas import NormalizedSearchResult, SearchQuerySpec
from app.integrations.tavily_client import TavilyIntegrationError
from app.logging_config import get_logger
from app.research.search_discovery import generate_alternative_query
from app.resilience.fallback_manager import try_in_order

logger = get_logger(__name__)

SearchFn = Callable[..., Awaitable[list[NormalizedSearchResult]]]

MAX_ALTERNATIVE_ATTEMPTS = 2


def _strategy_for(search_fn: SearchFn, spec: SearchQuerySpec) -> Callable[[], Awaitable[list[NormalizedSearchResult]]]:
    async def _run() -> list[NormalizedSearchResult]:
        return await search_fn(spec.query, category_hint=spec.category_hint, max_results=spec.max_results)

    return _run


async def run_queries(
    search_fn: SearchFn,
    specs: list[SearchQuerySpec],
) -> tuple[list[NormalizedSearchResult], list[str]]:
    """Run each query spec against the given Tavily search method.

    Implements EC-06 (Tavily returns zero results): if a query returns nothing, try a
    bounded number of alternative formulations - via the shared fallback-chain runner -
    before giving up on that query. Individual query failures (API errors) are recorded
    and do not abort the other queries.
    """
    all_results: list[NormalizedSearchResult] = []
    failed_queries: list[str] = []

    for spec in specs:
        alternatives = [spec] + [
            generate_alternative_query(spec, attempt) for attempt in range(1, MAX_ALTERNATIVE_ATTEMPTS + 1)
        ]
        strategies = [
            (f"attempt-{i}:{q.query}", _strategy_for(search_fn, q)) for i, q in enumerate(alternatives)
        ]

        try:
            outcome = await try_in_order(strategies, is_acceptable=bool)
        except TavilyIntegrationError as exc:
            logger.warning("query_runner.query_failed", query=spec.query, error=str(exc))
            failed_queries.append(spec.query)
            continue
        except ValueError:
            logger.info("query_runner.no_results_after_alternatives", query=spec.query)
            continue

        if outcome.strategy_used != strategies[0][0]:
            logger.info(
                "query_runner.zero_results_retry_succeeded",
                original_query=spec.query, strategy_used=outcome.strategy_used,
            )
        all_results.extend(outcome.value)

    return all_results, failed_queries
