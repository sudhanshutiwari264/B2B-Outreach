import json
import os
from pathlib import Path

os.environ["DATABASE_URL"] = "postgresql+asyncpg://outreach:outreach@localhost:5432/outreach_test"
os.environ["DATABASE_URL_SYNC"] = "postgresql+psycopg://outreach:outreach@localhost:5432/outreach_test"
os.environ.setdefault("TARQA_API_KEY", "")
os.environ.setdefault("TARQA_BASE_URL", "")
os.environ.setdefault("TARQA_MODEL", "")
os.environ.setdefault("TAVILY_API_KEY", "")

import psycopg
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import Base

get_settings.cache_clear()

SAMPLE_DATA_DIR = Path(__file__).resolve().parents[1] / "sample_data"


def _ensure_test_database_exists() -> None:
    admin_conn = psycopg.connect(
        "postgresql://outreach:outreach@localhost:5432/outreach", autocommit=True
    )
    try:
        with admin_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'outreach_test'")
            if cur.fetchone() is None:
                cur.execute("CREATE DATABASE outreach_test OWNER outreach")
    finally:
        admin_conn.close()


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    _ensure_test_database_exists()
    settings = get_settings()
    engine = create_async_engine(settings.database_url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with db_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


def load_sample_prospects() -> list[dict]:
    with open(SAMPLE_DATA_DIR / "prospects.json") as f:
        return json.load(f)


def load_sample_sources_and_signals() -> dict:
    with open(SAMPLE_DATA_DIR / "sources_and_signals.json") as f:
        return json.load(f)


def get_sample_prospect(scenario: str) -> dict:
    for entry in load_sample_prospects():
        if entry["scenario"] == scenario:
            return entry["prospect"]
    raise KeyError(f"No sample prospect for scenario {scenario!r}")


def get_sample_fixture(scenario: str) -> dict:
    return load_sample_sources_and_signals()[scenario]


async def create_prospect_and_execution(db_session, prospect_dict: dict):
    from app.models.enums import ExecutionStatus
    from app.models.execution import Execution
    from app.models.prospect import Prospect

    prospect = Prospect(**prospect_dict)
    db_session.add(prospect)
    await db_session.flush()

    execution = Execution(prospect_id=prospect.id, status=ExecutionStatus.QUEUED)
    db_session.add(execution)
    await db_session.commit()
    await db_session.refresh(execution)
    return prospect, execution
