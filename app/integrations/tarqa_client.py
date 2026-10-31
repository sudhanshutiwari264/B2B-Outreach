from typing import Optional, TypeVar

from openai import APIError, APIStatusError, APITimeoutError, AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings
from app.logging_config import get_logger
from app.resilience.retry_manager import RetryExhaustedError, retry_with_backoff
from app.validation.llm_output_validator import parse_structured_output

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

_TRANSIENT_EXCEPTIONS = (APITimeoutError, APIStatusError, APIError)


class TarqaIntegrationError(Exception):
    """Raised when Tarqa AI cannot be reached or returns an unusable response."""


class TarqaNotConfiguredError(TarqaIntegrationError):
    """Raised when TARQA_API_KEY / TARQA_BASE_URL / TARQA_MODEL are missing."""


class TarqaOutputValidationError(TarqaIntegrationError):
    """Raised when the LLM's output could not be parsed/validated as the requested schema,
    even after corrective retries. The caller must treat this as a failed extraction, not
    fabricate a fallback result.
    """


class TarqaClient:
    """Wrapper around Tarqa AI's OpenAI-compatible gateway, using the official OpenAI SDK.

    Confirmed against the live gateway: base_url = f"{TARQA_BASE_URL}/v1", bearer auth via
    TARQA_API_KEY, standard /chat/completions and /models endpoints. response_format
    json_object is accepted but some models still wrap output in markdown code fences, so
    output is always defensively unwrapped and Pydantic-validated rather than trusted blindly.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        if not self._settings.tarqa_configured:
            self._sdk: Optional[AsyncOpenAI] = None
        else:
            base_url = self._settings.tarqa_base_url.rstrip("/") + "/v1"
            self._sdk = AsyncOpenAI(
                api_key=self._settings.tarqa_api_key,
                base_url=base_url,
                timeout=self._settings.llm_timeout_seconds,
            )
        self._default_model = self._settings.tarqa_model

    @property
    def is_configured(self) -> bool:
        return self._sdk is not None

    def _require_sdk(self) -> AsyncOpenAI:
        if self._sdk is None:
            raise TarqaNotConfiguredError(
                "TARQA_API_KEY / TARQA_BASE_URL / TARQA_MODEL are not fully set. "
                "Add them to your .env to enable LLM-powered signal extraction and drafting."
            )
        return self._sdk

    async def test_connection(self) -> dict:
        sdk = self._require_sdk()
        try:
            resp = await sdk.chat.completions.create(
                model=self._default_model,
                messages=[{"role": "user", "content": "Reply with exactly: pong"}],
                max_tokens=5,
            )
            content = (resp.choices[0].message.content or "").strip()
            return {"ok": True, "model": self._default_model, "response": content}
        except Exception as exc:  # noqa: BLE001
            logger.error("tarqa.test_connection_failed", error=str(exc))
            return {"ok": False, "model": self._default_model, "error": str(exc)}

    async def list_models(self) -> list[dict]:
        sdk = self._require_sdk()
        try:
            resp = await sdk.models.list()
        except Exception as exc:  # noqa: BLE001
            raise TarqaIntegrationError(str(exc)) from exc
        return [m.model_dump() for m in resp.data]

    async def generate_completion(
        self,
        messages: list[dict],
        *,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.4,
        max_attempts: Optional[int] = None,
    ) -> str:
        sdk = self._require_sdk()
        use_model = model or self._default_model
        attempts = max_attempts or self._settings.llm_max_retries

        async def _attempt() -> str:
            resp = await sdk.chat.completions.create(
                model=use_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content or ""

        try:
            return await retry_with_backoff(
                _attempt, max_attempts=attempts, retriable_exceptions=_TRANSIENT_EXCEPTIONS
            )
        except RetryExhaustedError as exc:
            logger.error("tarqa.generate_completion_failed", error=str(exc.last_error))
            raise TarqaIntegrationError(str(exc.last_error)) from exc

    async def generate_structured_output(
        self,
        messages: list[dict],
        response_model: type[T],
        *,
        model: Optional[str] = None,
        max_tokens: int = 1500,
        temperature: float = 0.2,
        max_json_repair_attempts: int = 2,
    ) -> T:
        """Request JSON-mode output and validate it against response_model.

        Never returns a fabricated/best-guess result: if the model's output cannot be
        parsed and validated after corrective retries, raises TarqaOutputValidationError.
        """
        sdk = self._require_sdk()
        use_model = model or self._default_model
        working_messages = list(messages)
        last_error: Optional[Exception] = None

        for round_idx in range(max_json_repair_attempts + 1):

            async def _attempt() -> str:
                resp = await sdk.chat.completions.create(
                    model=use_model,
                    messages=working_messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                return resp.choices[0].message.content or ""

            try:
                raw = await retry_with_backoff(
                    _attempt,
                    max_attempts=self._settings.llm_max_retries,
                    retriable_exceptions=_TRANSIENT_EXCEPTIONS,
                )
            except RetryExhaustedError as exc:
                logger.error("tarqa.structured_output_api_failed", error=str(exc.last_error))
                raise TarqaIntegrationError(str(exc.last_error)) from exc

            try:
                return parse_structured_output(raw, response_model)
            except (ValueError, ValidationError) as exc:
                last_error = exc
                logger.warning(
                    "tarqa.structured_output_invalid",
                    round=round_idx,
                    error=str(exc),
                    raw_snippet=raw[:300],
                )
                working_messages = working_messages + [
                    {"role": "assistant", "content": raw},
                    {
                        "role": "user",
                        "content": (
                            "Your previous response was not valid JSON matching the required "
                            f"schema. Error: {exc}. Respond with ONLY a single valid JSON object "
                            "matching the schema, no markdown fences, no commentary."
                        ),
                    },
                ]
                continue

        raise TarqaOutputValidationError(
            f"LLM output failed schema validation after {max_json_repair_attempts + 1} attempts: {last_error}"
        )
