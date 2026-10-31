import json
import re
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def strip_markdown_fence(text: str) -> str:
    """Some models wrap JSON-mode output in ```json ... ``` fences even when asked not
    to; this unwraps it so json.loads doesn't choke on it (EC-10)."""
    text = text.strip()
    match = _JSON_FENCE_RE.match(text)
    if match:
        return match.group(1).strip()
    return text


def parse_structured_output(raw: str, schema: type[T]) -> T:
    """Strict parse + Pydantic validation of one LLM response against a schema.

    Raises json.JSONDecodeError or pydantic.ValidationError on failure - callers decide
    whether/how to retry with a corrective prompt (EC-09/EC-10). This function never
    guesses at or repairs malformed JSON itself; it only ever accepts exactly what the
    schema requires, so a caller can never silently accept a malformed AI response.
    """
    cleaned = strip_markdown_fence(raw)
    parsed = json.loads(cleaned)
    return schema.model_validate(parsed)
