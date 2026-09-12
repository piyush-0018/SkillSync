from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.interview_session import InterviewSession


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence_number", name="uq_interview_questions_session_sequence"),
        CheckConstraint("sequence_number > 0", name="ck_interview_questions_sequence"),
        CheckConstraint("score IS NULL OR score BETWEEN 0 AND 100", name="ck_interview_questions_score"),
        Index("ix_interview_questions_session_asked", "session_id", "asked_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True
    )
    sequence_number: Mapped[int]
    question_text: Mapped[str] = mapped_column(Text)
    focus_area: Mapped[str] = mapped_column(String(120))
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped[InterviewSession] = relationship(back_populates="questions")
