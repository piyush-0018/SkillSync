"""create resume analyses table

Revision ID: 20260827_03
Revises: 20260827_02
Create Date: 2026-08-27
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260827_03"
down_revision: str | None = "20260827_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resume_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("resume_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("category_scores", sa.JSON(), nullable=False),
        sa.Column("analysis_result", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("provider_response_id", sa.String(length=100), nullable=True),
        sa.Column("rubric_version", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("overall_score BETWEEN 0 AND 100", name="ck_resume_analyses_overall_score"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resume_analyses_resume_id"), "resume_analyses", ["resume_id"], unique=False)
    op.create_index(op.f("ix_resume_analyses_resume_fingerprint"), "resume_analyses", ["resume_fingerprint"], unique=False)
    op.create_index("ix_resume_analyses_resume_created", "resume_analyses", ["resume_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_resume_analyses_resume_created", table_name="resume_analyses")
    op.drop_index(op.f("ix_resume_analyses_resume_fingerprint"), table_name="resume_analyses")
    op.drop_index(op.f("ix_resume_analyses_resume_id"), table_name="resume_analyses")
    op.drop_table("resume_analyses")
