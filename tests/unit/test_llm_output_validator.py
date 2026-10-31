import json

import pytest
from pydantic import BaseModel, ValidationError

from app.validation.llm_output_validator import parse_structured_output, strip_markdown_fence


class Sample(BaseModel):
    ok: bool
    message: str


def test_strip_markdown_fence_removes_json_fence():
    raw = '```json\n{"ok": true, "message": "hi"}\n```'
    assert strip_markdown_fence(raw) == '{"ok": true, "message": "hi"}'


def test_strip_markdown_fence_passthrough_when_no_fence():
    raw = '{"ok": true}'
    assert strip_markdown_fence(raw) == raw


def test_parse_structured_output_valid_json():
    raw = json.dumps({"ok": True, "message": "hello"})
    result = parse_structured_output(raw, Sample)
    assert result.ok is True
    assert result.message == "hello"


def test_parse_structured_output_handles_fenced_json():
    raw = '```json\n{"ok": false, "message": "wrapped"}\n```'
    result = parse_structured_output(raw, Sample)
    assert result.message == "wrapped"


def test_parse_structured_output_rejects_malformed_json():
    """EC-10: malformed JSON must raise, never be silently accepted."""
    with pytest.raises(json.JSONDecodeError):
        parse_structured_output("{not valid json", Sample)


def test_parse_structured_output_rejects_schema_mismatch():
    raw = json.dumps({"wrong_field": 123})
    with pytest.raises(ValidationError):
        parse_structured_output(raw, Sample)
