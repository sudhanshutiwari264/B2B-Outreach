import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.draft import OutreachDraft
from app.models.enums import DraftStatus
from app.schemas.draft import DraftEditRequest, DraftRead, DraftRejectRequest

router = APIRouter(prefix="/api/v1/outreach", tags=["outreach"])

_TERMINAL_STATUSES = {DraftStatus.APPROVED, DraftStatus.REJECTED}


@router.get("", response_model=list[DraftRead])
async def list_drafts(
    status_filter: DraftStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[OutreachDraft]:
    """List drafts across all executions, most recent first - used by the dashboard for
    pending-review / approved counts without requiring an execution id up front."""
    query = select(OutreachDraft).order_by(OutreachDraft.created_at.desc()).limit(limit).offset(offset)
    if status_filter is not None:
        query = query.where(OutreachDraft.status == status_filter)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{execution_id}", response_model=list[DraftRead])
async def get_execution_drafts(execution_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[OutreachDraft]:
    result = await db.execute(
        select(OutreachDraft).where(OutreachDraft.execution_id == execution_id)
    )
    drafts = list(result.scalars().all())
    if not drafts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No drafts found for this execution")

    changed = False
    for d in drafts:
        if d.status == DraftStatus.DRAFT_GENERATED:
            d.status = DraftStatus.PENDING_REVIEW
            changed = True
    if changed:
        await db.commit()
    return drafts


async def _get_draft_or_404(draft_id: uuid.UUID, db: AsyncSession) -> OutreachDraft:
    draft = await db.get(OutreachDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return draft


@router.patch("/{draft_id}", response_model=DraftRead)
async def edit_draft(
    draft_id: uuid.UUID, payload: DraftEditRequest, db: AsyncSession = Depends(get_db)
) -> OutreachDraft:
    draft = await _get_draft_or_404(draft_id, db)
    if draft.status in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Draft is already {draft.status.value} and can no longer be edited",
        )
    draft.edited_subject = payload.subject
    draft.edited_body = payload.body
    draft.reviewer_notes = payload.reviewer_notes
    draft.status = DraftStatus.EDITED
    await db.commit()
    await db.refresh(draft)
    return draft


@router.post("/{draft_id}/approve", response_model=DraftRead)
async def approve_draft(draft_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> OutreachDraft:
    """Marks the draft approved for sending by a human. This system never sends outreach
    itself - approval only records the human decision; email/LinkedIn delivery is outside
    this project's scope (section 14)."""
    draft = await _get_draft_or_404(draft_id, db)
    if draft.status in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Draft is already {draft.status.value}",
        )
    draft.status = DraftStatus.APPROVED
    await db.commit()
    await db.refresh(draft)
    return draft


@router.post("/{draft_id}/reject", response_model=DraftRead)
async def reject_draft(
    draft_id: uuid.UUID, payload: DraftRejectRequest, db: AsyncSession = Depends(get_db)
) -> OutreachDraft:
    draft = await _get_draft_or_404(draft_id, db)
    if draft.status in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Draft is already {draft.status.value}",
        )
    draft.status = DraftStatus.REJECTED
    draft.reviewer_notes = payload.reviewer_notes
    await db.commit()
    await db.refresh(draft)
    return draft
