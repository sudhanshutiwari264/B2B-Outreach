from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from app.config import Settings
from app.integrations.tarqa_client import (
    TarqaClient,
    TarqaNotConfiguredError,
    TarqaOutputValidationError,
)


class Ping(BaseModel):
    ok: bool
    message: str


def _client_with_fake_sdk() -> TarqaClient:
    settings = Settings(
        tarqa_api_key="fake-key", tarqa_base_url="https://fake.tarqaai.example.com/api",
        tarqa_model="fake-model",
    )
    client = TarqaClient(settings)
    client._sdk = MagicMock()
    client._sdk.chat = MagicMock()
    client._sdk.chat.completions = MagicMock()
    return client


def _completion_with_content(content: str):
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


async def test_not_configured_raises_clear_error():
    settings = Settings(tarqa_api_key=None, tarqa_base_url=None, tarqa_model=None)
    client = TarqaClient(settings)
    assert client.is_configured is False
    with pytest.raises(TarqaNotConfiguredError):
        await client.generate_completion([{"role": "user", "content": "hi"}])


async def test_generate_completion_returns_message_content():
    client = _client_with_fake_sdk()
    client._sdk.chat.completions.create = AsyncMock(
        return_value=_completion_with_content("hello there")
    )
    result = await client.generate_completion([{"role": "user", "content": "hi"}])
    assert result == "hello there"


async def test_generate_structured_output_parses_clean_json():
    client = _client_with_fake_sdk()
    client._sdk.chat.completions.create = AsyncMock(
        return_value=_completion_with_content('{"ok": true, "message": "hi"}')
    )
    result = await client.generate_structured_output([{"role": "user", "content": "go"}], Ping)
    assert result.ok is True


async def test_generate_structured_output_strips_markdown_fence():
    client = _client_with_fake_sdk()
    client._sdk.chat.completions.create = AsyncMock(
        return_value=_completion_with_content('```json\n{"ok": false, "message": "wrapped"}\n```')
    )
    result = await client.generate_structured_output([{"role": "user", "content": "go"}], Ping)
    assert result.message == "wrapped"


async def test_generate_structured_output_retries_on_invalid_json_then_succeeds():
    """EC-10: invalid JSON triggers a corrective retry; a later valid response is accepted."""
    client = _client_with_fake_sdk()
    client._sdk.chat.completions.create = AsyncMock(
        side_effect=[
            _completion_with_content("not json at all"),
            _completion_with_content('{"ok": true, "message": "fixed"}'),
        ]
    )
    result = await client.generate_structured_output(
        [{"role": "user", "content": "go"}], Ping, max_json_repair_attempts=2
    )
    assert result.message == "fixed"
    assert client._sdk.chat.completions.create.call_count == 2


async def test_generate_structured_output_gives_up_after_max_repair_attempts():
    """EC-10: never silently accept malformed output - raise once retries are exhausted."""
    client = _client_with_fake_sdk()
    client._sdk.chat.completions.create = AsyncMock(
        return_value=_completion_with_content("still not json")
    )
    with pytest.raises(TarqaOutputValidationError):
        await client.generate_structured_output(
            [{"role": "user", "content": "go"}], Ping, max_json_repair_attempts=1
        )
