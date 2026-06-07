"""Patient profile: GET / PUT."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import PatientProfile
from app.models.schemas import PatientProfileResponse, PatientProfileUpdate
from app.routers.auth import get_current_user_id_required

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=PatientProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user_id_required),
    session: AsyncSession = Depends(get_db),
):
    """Get current user's patient profile. Creates empty profile if missing."""
    result = await session.execute(
        select(PatientProfile).where(PatientProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = PatientProfile(user_id=user_id)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    return PatientProfileResponse(
        user_id=profile.user_id,
        name=profile.name or "",
        age=profile.age,
        sex=profile.sex or "",
        allergies=profile.allergies or "",
        conditions=profile.conditions or "",
        medications=profile.medications or "",
        preferences=profile.preferences or "",
    )


@router.put("", response_model=PatientProfileResponse)
async def update_profile(
    body: PatientProfileUpdate,
    user_id: str = Depends(get_current_user_id_required),
    session: AsyncSession = Depends(get_db),
):
    """Update current user's patient profile."""
    result = await session.execute(
        select(PatientProfile).where(PatientProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = PatientProfile(user_id=user_id)
        session.add(profile)
        await session.flush()
    profile.name = body.name
    profile.age = body.age
    profile.sex = body.sex
    profile.allergies = body.allergies
    profile.conditions = body.conditions
    profile.medications = body.medications
    profile.preferences = body.preferences
    await session.commit()
    await session.refresh(profile)
    return PatientProfileResponse(
        user_id=profile.user_id,
        name=profile.name or "",
        age=profile.age,
        sex=profile.sex or "",
        allergies=profile.allergies or "",
        conditions=profile.conditions or "",
        medications=profile.medications or "",
        preferences=profile.preferences or "",
    )
