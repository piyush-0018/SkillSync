from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.resume import Resume


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"
    __table_args__ = (
        CheckConstraint("overall_score BETWEEN 0 AND 100", name="ck_resume_analyses_overall_score"),
        Index("ix_resume_analyses_resume_created", "resume_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    resume_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    overall_score: Mapped[int]
    category_scores: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    analysis_result: Mapped[dict[str, Any]] = mapped_column(JSON)
    provider: Mapped[str] = mapped_column(String(30))
    model_name: Mapped[str] = mapped_column(String(100))
    provider_response_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rubric_version: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    resume: Mapped[Resume] = relationship(back_populates="analyses")
