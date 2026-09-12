"""create career assistant tables

Revision ID: 20260905_05
Revises: 20260830_04
Create Date: 2026-09-05
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260905_05"
down_revision: str | None = "20260830_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "career_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("source_record_id", sa.Integer(), nullable=True),
        sa.Column("source_key", sa.String(length=180), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("source_attributes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "source_type IN ('profile', 'resume', 'resume_analysis', 'job_match')",
            name="ck_career_documents_source_type",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "source_key", name="uq_career_documents_user_source_key"),
    )
    op.create_index(op.f("ix_career_documents_user_id"), "career_documents", ["user_id"], unique=False)
    op.create_index("ix_career_documents_user_source", "career_documents", ["user_id", "source_type"], unique=False)

    op.create_table(
        "career_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("chunk_index >= 0", name="ck_career_chunks_chunk_index"),
        sa.ForeignKeyConstraint(["document_id"], ["career_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_career_chunks_document_index"),
    )
    op.create_index(op.f("ix_career_chunks_document_id"), "career_chunks", ["document_id"], unique=False)
    op.create_index(op.f("ix_career_chunks_user_id"), "career_chunks", ["user_id"], unique=False)
    op.create_index("ix_career_chunks_user_model", "career_chunks", ["user_id", "embedding_model"], unique=False)

    op.create_table(
        "career_conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_career_conversations_user_id"), "career_conversations", ["user_id"], unique=False)
    op.create_index(
        "ix_career_conversations_user_updated",
        "career_conversations",
        ["user_id", "updated_at"],
        unique=False,
    )

    op.create_table(
        "career_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("grounding_mode", sa.String(length=20), nullable=True),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_career_messages_role"),
        sa.CheckConstraint(
            "grounding_mode IS NULL OR grounding_mode IN ('user_data', 'general', 'mixed')",
            name="ck_career_messages_grounding_mode",
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["career_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_career_messages_conversation_id"), "career_messages", ["conversation_id"], unique=False)
    op.create_index(
        "ix_career_messages_conversation_created",
        "career_messages",
        ["conversation_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_career_messages_conversation_created", table_name="career_messages")
    op.drop_index(op.f("ix_career_messages_conversation_id"), table_name="career_messages")
    op.drop_table("career_messages")
    op.drop_index("ix_career_conversations_user_updated", table_name="career_conversations")
    op.drop_index(op.f("ix_career_conversations_user_id"), table_name="career_conversations")
    op.drop_table("career_conversations")
    op.drop_index("ix_career_chunks_user_model", table_name="career_chunks")
    op.drop_index(op.f("ix_career_chunks_user_id"), table_name="career_chunks")
    op.drop_index(op.f("ix_career_chunks_document_id"), table_name="career_chunks")
    op.drop_table("career_chunks")
    op.drop_index("ix_career_documents_user_source", table_name="career_documents")
    op.drop_index(op.f("ix_career_documents_user_id"), table_name="career_documents")
    op.drop_table("career_documents")
