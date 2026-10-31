from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models  # noqa: F401  ensures all ORM mappers are registered before first use
from app.api import executions, health, outreach, prospects, research
from app.config import get_settings
from app.logging_config import configure_logging, get_logger
from app.resilience.error_handler import safe_error_message

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Personalized Outreach Intelligence Engine",
    description=(
        "AI-powered B2B research and personalized outreach drafting backend. "
        "Research -> signal extraction -> scoring -> conflict detection -> "
        "evidence-backed outreach drafts, with mandatory human review before sending."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(prospects.router)
app.include_router(research.router)
app.include_router(executions.router)
app.include_router(outreach.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Never leak internal exception details (API keys, stack traces, SQL) to clients."""
    logger.exception("unhandled_exception", path=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"detail": safe_error_message(exc, default="An internal error occurred")},
    )
