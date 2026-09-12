from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.career_conversation import CareerConversation
    from app.models.career_document import CareerDocument
    from app.models.job_match import JobMatch
    from app.models.interview_session import InterviewSession
    from app.models.resume import Resume


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "experience_level IS NULL OR experience_level IN ('student', 'fresher', '0-1 years', '1-3 years', '3+ years')",
            name="ck_users_experience_level",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    target_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resume: Mapped[Resume | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    job_matches: Mapped[list[JobMatch]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    career_documents: Mapped[list[CareerDocument]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    career_conversations: Mapped[list[CareerConversation]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    interview_sessions: Mapped[list[InterviewSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
