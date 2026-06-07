"""SQLAlchemy models for User and PatientProfile."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, String, Text, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base for all models."""

    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped[Optional["PatientProfile"]] = relationship(
        "PatientProfile", back_populates="user", uselist=False
    )


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(255), default="")
    age: Mapped[Optional[int]] = mapped_column(nullable=True)
    sex: Mapped[str] = mapped_column(String(50), default="")
    allergies: Mapped[str] = mapped_column(Text, default="")
    conditions: Mapped[str] = mapped_column(Text, default="")
    medications: Mapped[str] = mapped_column(Text, default="")
    preferences: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class Consultation(Base):
    """One exchange (user message + assistant response) for history."""

    __tablename__ = "consultations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), default="")
    messages: Mapped[Any] = mapped_column(JSON, default=list)  # list of {role, content, ...}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
