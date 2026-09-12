from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.career_conversation import CareerConversation


class CareerMessage(Base):
    __tablename__ = "career_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_career_messages_role"),
        CheckConstraint(
            "grounding_mode IS NULL OR grounding_mode IN ('user_data', 'general', 'mixed')",
            name="ck_career_messages_grounding_mode",
        ),
        Index("ix_career_messages_conversation_created", "conversation_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("career_conversations.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    grounding_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    provider: Mapped[str | None] = mapped_column(String(30), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[CareerConversation] = relationship(back_populates="messages")
