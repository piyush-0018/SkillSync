from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.career_chunk import CareerChunk
    from app.models.user import User


class CareerDocument(Base):
    __tablename__ = "career_documents"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('profile', 'resume', 'resume_analysis', 'job_match')",
            name="ck_career_documents_source_type",
        ),
        UniqueConstraint("user_id", "source_key", name="uq_career_documents_user_source_key"),
        Index("ix_career_documents_user_source", "user_id", "source_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(30))
    source_record_id: Mapped[int | None] = mapped_column(nullable=True)
    source_key: Mapped[str] = mapped_column(String(180))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    content_fingerprint: Mapped[str] = mapped_column(String(64))
    source_attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="career_documents")
    chunks: Mapped[list[CareerChunk]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CareerChunk.chunk_index",
    )
