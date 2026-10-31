import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RetryExhaustedError(Exception):
    def __init__(self, attempts: int, last_error: Exception):
        super().__init__(f"Retry exhausted after {attempts} attempts: {last_error}")
        self.attempts = attempts
        self.last_error = last_error


async def retry_with_backoff(
    fn: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    retriable_exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
) -> T:
    """Bounded exponential backoff with jitter. Never retries indefinitely.

    Raises RetryExhaustedError (wrapping the last exception) once max_attempts is reached.
    """
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn()
        except retriable_exceptions as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= max_attempts:
                break
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay = delay * (0.5 + random.random())
            logger.warning(
                "retry_with_backoff.retrying",
                attempt=attempt,
                max_attempts=max_attempts,
                delay_seconds=round(delay, 2),
                error=str(exc),
            )
            if on_retry:
                on_retry(attempt, exc)
            await asyncio.sleep(delay)

    assert last_error is not None
    raise RetryExhaustedError(max_attempts, last_error)
