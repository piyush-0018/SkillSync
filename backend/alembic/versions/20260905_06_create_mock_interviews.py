"""create mock interview tables

Revision ID: 20260905_06
Revises: 20260905_05
Create Date: 2026-09-05
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260905_06"
down_revision: str | None = "20260905_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("target_role", sa.String(length=100), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("interview_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("question_limit", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("final_feedback", sa.JSON(), nullable=True),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced')",
            name="ck_interview_sessions_difficulty",
        ),
        sa.CheckConstraint(
            "interview_type IN ('technical', 'behavioral', 'resume_based', 'mixed')",
            name="ck_interview_sessions_type",
        ),
        sa.CheckConstraint("status IN ('active', 'completed')", name="ck_interview_sessions_status"),
        sa.CheckConstraint("question_limit BETWEEN 1 AND 10", name="ck_interview_sessions_question_limit"),
        sa.CheckConstraint(
            "overall_score IS NULL OR overall_score BETWEEN 0 AND 100",
            name="ck_interview_sessions_overall_score",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_sessions_user_id"), "interview_sessions", ["user_id"], unique=False)
    op.create_index(
        "ix_interview_sessions_user_created", "interview_sessions", ["user_id", "created_at"], unique=False
    )

    op.create_table(
        "interview_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("focus_area", sa.String(length=120), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("evaluation", sa.JSON(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("asked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("sequence_number > 0", name="ck_interview_questions_sequence"),
        sa.CheckConstraint("score IS NULL OR score BETWEEN 0 AND 100", name="ck_interview_questions_score"),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "sequence_number", name="uq_interview_questions_session_sequence"),
    )
    op.create_index(op.f("ix_interview_questions_session_id"), "interview_questions", ["session_id"], unique=False)
    op.create_index(
        "ix_interview_questions_session_asked", "interview_questions", ["session_id", "asked_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_interview_questions_session_asked", table_name="interview_questions")
    op.drop_index(op.f("ix_interview_questions_session_id"), table_name="interview_questions")
    op.drop_table("interview_questions")
    op.drop_index("ix_interview_sessions_user_created", table_name="interview_sessions")
    op.drop_index(op.f("ix_interview_sessions_user_id"), table_name="interview_sessions")
    op.drop_table("interview_sessions")
