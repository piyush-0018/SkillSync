from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.job_match import JobMatch
    from app.models.resume_analysis import ResumeAnalysis
    from app.models.user import User


class Resume(Base):
    __tablename__ = "resumes"
    __table_args__ = (
        CheckConstraint("parsing_status IN ('parsed', 'failed')", name="ck_resumes_parsing_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(64), unique=True)
    file_size: Mapped[int]
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    parsed_text: Mapped[str] = mapped_column(Text, default="")
    structured_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    parsing_status: Mapped[str] = mapped_column(String(20))
    parsing_error: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship(back_populates="resume")
    analyses: Mapped[list[ResumeAnalysis]] = relationship(
        back_populates="resume",
        cascade="all, delete-orphan",
    )
    job_matches: Mapped[list[JobMatch]] = relationship(back_populates="resume")
