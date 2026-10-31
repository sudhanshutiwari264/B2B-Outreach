import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.prospect import Prospect
from app.schemas.prospect import ProspectCreate, ProspectIdentityCheck, ProspectRead
from app.validation.prospect_validator import validate_prospect_identity

router = APIRouter(prefix="/api/v1/prospects", tags=["prospects"])


@router.post("", response_model=ProspectRead, status_code=status.HTTP_201_CREATED)
async def create_prospect(payload: ProspectCreate, db: AsyncSession = Depends(get_db)) -> Prospect:
    """Create a prospect. Note: a 201 here does not guarantee the prospect can be
    researched - identity ambiguity is (re-)checked when a research run is started via
    POST /api/v1/research/run, which returns an insufficient_data status rather than
    researching a potentially wrong person (EC-03/EC-11)."""
    row = Prospect(**payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("", response_model=list[ProspectRead])
async def list_prospects(
    limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)
) -> list[Prospect]:
    result = await db.execute(
        select(Prospect).order_by(Prospect.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all())


@router.get("/{prospect_id}", response_model=ProspectRead)
async def get_prospect(prospect_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Prospect:
    row = await db.get(Prospect, prospect_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found")
    return row


@router.get("/{prospect_id}/identity-check", response_model=ProspectIdentityCheck)
async def check_prospect_identity(
    prospect_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> ProspectIdentityCheck:
    row = await db.get(Prospect, prospect_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found")
    prospect = ProspectCreate(
        name=row.name, company=row.company, designation=row.designation,
        linkedin_url=row.linkedin_url, company_website=row.company_website,
        industry=row.industry, outreach_channel=row.outreach_channel,
        product_context=row.product_context,
    )
    return validate_prospect_identity(prospect)
