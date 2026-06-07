"""Consultation history: list and get by id."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Consultation
from app.models.schemas import ConsultationDetail, ConsultationSummary
from app.routers.auth import get_current_user_id_required

router = APIRouter(prefix="/api/consultations", tags=["consultations"])


@router.get("", response_model=list[ConsultationSummary])
async def list_consultations(
    user_id: str = Depends(get_current_user_id_required),
    session: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """List current user's consultations, newest first."""
    result = await session.execute(
        select(Consultation)
        .where(Consultation.user_id == user_id)
        .order_by(Consultation.created_at.desc())
        .limit(max(1, min(limit, 100)))
    )
    rows = result.scalars().all()
    return [
        ConsultationSummary(
            id=r.id,
            title=r.title or "Consultation",
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in rows
    ]


@router.get("/{consultation_id}", response_model=ConsultationDetail)
async def get_consultation(
    consultation_id: str,
    user_id: str = Depends(get_current_user_id_required),
    session: AsyncSession = Depends(get_db),
):
    """Get one consultation by id (must belong to current user)."""
    result = await session.execute(
        select(Consultation).where(
            Consultation.id == consultation_id,
            Consultation.user_id == user_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return ConsultationDetail(
        id=row.id,
        title=row.title or "Consultation",
        messages=row.messages or [],
        created_at=row.created_at.isoformat() if row.created_at else "",
    )
