from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.interview_question import InterviewQuestion
    from app.models.user import User


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced')",
            name="ck_interview_sessions_difficulty",
        ),
        CheckConstraint(
            "interview_type IN ('technical', 'behavioral', 'resume_based', 'mixed')",
            name="ck_interview_sessions_type",
        ),
        CheckConstraint(
            "response_mode IN ('text', 'video')",
            name="ck_interview_sessions_response_mode",
        ),
        CheckConstraint("status IN ('active', 'completed')", name="ck_interview_sessions_status"),
        CheckConstraint("question_limit BETWEEN 1 AND 10", name="ck_interview_sessions_question_limit"),
        CheckConstraint(
            "overall_score IS NULL OR overall_score BETWEEN 0 AND 100",
            name="ck_interview_sessions_overall_score",
        ),
        Index("ix_interview_sessions_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_role: Mapped[str] = mapped_column(String(100))
    difficulty: Mapped[str] = mapped_column(String(20))
    interview_type: Mapped[str] = mapped_column(String(20))
    response_mode: Mapped[str] = mapped_column(String(20), default="text")
    status: Mapped[str] = mapped_column(String(20), default="active")
    question_limit: Mapped[int] = mapped_column(default=5)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_feedback: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    provider: Mapped[str] = mapped_column(String(30), default="gemini")
    model_name: Mapped[str] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="interview_sessions")
    questions: Mapped[list[InterviewQuestion]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="InterviewQuestion.sequence_number",
    )
