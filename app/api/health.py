from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.session import get_db
from app.integrations.tarqa_client import TarqaClient
from app.integrations.tavily_client import TavilyClient

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}


@router.get("/health/integrations")
async def health_integrations() -> dict:
    settings = get_settings()
    result: dict = {
        "tavily": {"configured": settings.tavily_configured},
        "tarqa": {"configured": settings.tarqa_configured},
    }

    tavily = TavilyClient(settings)
    if tavily.is_configured:
        try:
            results = await tavily.search_web("test connectivity", max_results=1)
            result["tavily"]["reachable"] = True
            result["tavily"]["sample_result_count"] = len(results)
        except Exception as exc:  # noqa: BLE001
            result["tavily"]["reachable"] = False
            result["tavily"]["error"] = str(exc)[:300]

    tarqa = TarqaClient(settings)
    if tarqa.is_configured:
        connection_result = await tarqa.test_connection()
        result["tarqa"]["reachable"] = connection_result.get("ok", False)
        result["tarqa"]["model"] = connection_result.get("model")
        if not connection_result.get("ok"):
            result["tarqa"]["error"] = str(connection_result.get("error"))[:300]

    return result
