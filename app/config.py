from functools import lru_cache
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _with_driver(url: str, driver: str) -> str:
    """Force a postgres connection string onto a specific SQLAlchemy driver, regardless of
    what scheme it arrived with. Handles the plain "postgres://"/"postgresql://" strings
    that most PaaS hosts (Render, Heroku, Railway) auto-generate for a provisioned
    database - those have no async/sync driver info at all, so without this the app would
    require a manual edit of every connection string after every deploy.
    """
    scheme, _, rest = url.partition("://")
    base_scheme = scheme.split("+", 1)[0]
    if base_scheme == "postgres":
        base_scheme = "postgresql"
    return f"{base_scheme}+{driver}://{rest}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://outreach:outreach@localhost:5432/outreach"
    # Left unset by default so the validator below can tell "not provided" apart from
    # "explicitly set" and derive it from database_url when needed.
    database_url_sync: Optional[str] = None

    tavily_api_key: Optional[str] = None

    tarqa_api_key: Optional[str] = None
    tarqa_base_url: Optional[str] = None
    tarqa_model: Optional[str] = None

    http_timeout_seconds: float = 15.0
    http_max_retries: int = 3
    llm_max_retries: int = 3
    llm_timeout_seconds: float = 60.0
    max_content_bytes: int = 2_000_000
    max_concurrent_extractions: int = 5

    @model_validator(mode="after")
    def _normalize_database_urls(self) -> "Settings":
        self.database_url = _with_driver(self.database_url, "asyncpg")
        self.database_url_sync = _with_driver(
            self.database_url_sync or self.database_url, "psycopg"
        )
        return self

    @property
    def tavily_configured(self) -> bool:
        return bool(self.tavily_api_key)

    @property
    def tarqa_configured(self) -> bool:
        return bool(self.tarqa_api_key and self.tarqa_base_url and self.tarqa_model)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
