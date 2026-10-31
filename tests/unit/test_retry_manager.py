import pytest

from app.resilience.retry_manager import RetryExhaustedError, retry_with_backoff


async def test_retry_with_backoff_succeeds_after_transient_failures():
    attempts = {"count": 0}

    async def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("transient")
        return "ok"

    result = await retry_with_backoff(flaky, max_attempts=5, base_delay=0.01, max_delay=0.02)
    assert result == "ok"
    assert attempts["count"] == 3


async def test_retry_with_backoff_never_retries_indefinitely():
    """EC-09: Tarqa/API failures must respect a maximum retry limit, never loop forever."""
    attempts = {"count": 0}

    async def always_fails():
        attempts["count"] += 1
        raise ValueError("permanent failure")

    with pytest.raises(RetryExhaustedError) as exc_info:
        await retry_with_backoff(always_fails, max_attempts=3, base_delay=0.01, max_delay=0.02)

    assert attempts["count"] == 3
    assert exc_info.value.attempts == 3


async def test_retry_with_backoff_only_catches_specified_exceptions():
    async def raises_type_error():
        raise TypeError("not retriable")

    with pytest.raises(TypeError):
        await retry_with_backoff(
            raises_type_error, max_attempts=3, base_delay=0.01,
            retriable_exceptions=(ValueError,),
        )
