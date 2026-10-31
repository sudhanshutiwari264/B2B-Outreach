from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from app.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class FallbackResult(Generic[T]):
    value: T
    strategy_used: str
    attempted_strategies: list[str]
    errors: dict[str, str]


async def try_in_order(
    strategies: list[tuple[str, Callable[[], Awaitable[T]]]],
    *,
    is_acceptable: Callable[[T], bool] = lambda result: True,
) -> FallbackResult[T]:
    """Try each (name, async_fn) strategy in order until one succeeds and is acceptable.

    Used e.g. for "Tavily Extract first, then local extraction fallback" (section 7) and
    for alternative query formulations when a search returns nothing useful (EC-06).
    Raises the last exception if every strategy fails or is rejected by is_acceptable.
    """
    attempted: list[str] = []
    errors: dict[str, str] = {}
    last_exc: Exception | None = None

    for name, fn in strategies:
        attempted.append(name)
        try:
            result = await fn()
        except Exception as exc:  # noqa: BLE001
            errors[name] = str(exc)
            last_exc = exc
            logger.warning("fallback_manager.strategy_failed", strategy=name, error=str(exc))
            continue

        if is_acceptable(result):
            return FallbackResult(
                value=result, strategy_used=name, attempted_strategies=attempted, errors=errors
            )
        errors[name] = "result rejected by acceptance check"
        logger.info("fallback_manager.strategy_rejected", strategy=name)

    if last_exc is not None:
        raise last_exc
    raise ValueError(f"All fallback strategies exhausted without an acceptable result: {attempted}")
