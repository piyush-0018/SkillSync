from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.career_document import CareerDocument


class CareerChunk(Base):
    __tablename__ = "career_chunks"
    __table_args__ = (
        CheckConstraint("chunk_index >= 0", name="ck_career_chunks_chunk_index"),
        UniqueConstraint("document_id", "chunk_index", name="uq_career_chunks_document_index"),
        Index("ix_career_chunks_user_model", "user_id", "embedding_model"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("career_documents.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int]
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(JSON)
    embedding_model: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[CareerDocument] = relationship(back_populates="chunks")
