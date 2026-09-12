from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.user import User


class JobMatch(Base):
    __tablename__ = "job_matches"
    __table_args__ = (
        CheckConstraint("overall_score BETWEEN 0 AND 100", name="ck_job_matches_overall_score"),
        Index("ix_job_matches_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    input_fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    job_title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    job_description: Mapped[str] = mapped_column(Text)
    parsed_job_requirements: Mapped[dict[str, Any]] = mapped_column(JSON)
    match_result: Mapped[dict[str, Any]] = mapped_column(JSON)
    overall_score: Mapped[int]
    provider: Mapped[str] = mapped_column(String(30))
    model_name: Mapped[str] = mapped_column(String(100))
    embedding_model: Mapped[str] = mapped_column(String(100))
    provider_response_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scoring_version: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="job_matches")
    resume: Mapped[Resume | None] = relationship(back_populates="job_matches")
