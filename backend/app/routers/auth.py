"""Auth: register, login, me."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token, decode_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import User
from app.models.schemas import TokenResponse, UserLogin, UserMe, UserRegister

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def get_current_user_id(
    authorization: str | None = Header(None, alias="Authorization"),
) -> str | None:
    """Extract user id from Bearer token. Returns None if no/invalid token."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return decode_token(token)


async def get_current_user_id_required(
    authorization: str | None = Header(None, alias="Authorization"),
) -> str:
    """Require valid token; raise 401 if missing/invalid."""
    user_id = await get_current_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return user_id


@router.post("/register", response_model=TokenResponse)
async def register(
    body: UserRegister,
    session: AsyncSession = Depends(get_db),
):
    """Register a new user. Returns access token."""
    result = await session.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return TokenResponse(access_token=create_access_token(user_id))


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLogin,
    session: AsyncSession = Depends(get_db),
):
    """Login; returns access token."""
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserMe)
async def me(
    user_id: str = Depends(get_current_user_id_required),
    session: AsyncSession = Depends(get_db),
):
    """Return current user (requires Bearer token)."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserMe(id=user.id, email=user.email)
