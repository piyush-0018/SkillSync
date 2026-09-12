"""create job matches table

Revision ID: 20260830_04
Revises: 20260827_03
Create Date: 2026-08-30
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260830_04"
down_revision: str | None = "20260827_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=True),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("job_title", sa.String(length=160), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("parsed_job_requirements", sa.JSON(), nullable=False),
        sa.Column("match_result", sa.JSON(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("provider_response_id", sa.String(length=100), nullable=True),
        sa.Column("scoring_version", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("overall_score BETWEEN 0 AND 100", name="ck_job_matches_overall_score"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_matches_user_id"), "job_matches", ["user_id"], unique=False)
    op.create_index(op.f("ix_job_matches_resume_id"), "job_matches", ["resume_id"], unique=False)
    op.create_index(op.f("ix_job_matches_input_fingerprint"), "job_matches", ["input_fingerprint"], unique=False)
    op.create_index("ix_job_matches_user_created", "job_matches", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_matches_user_created", table_name="job_matches")
    op.drop_index(op.f("ix_job_matches_input_fingerprint"), table_name="job_matches")
    op.drop_index(op.f("ix_job_matches_resume_id"), table_name="job_matches")
    op.drop_index(op.f("ix_job_matches_user_id"), table_name="job_matches")
    op.drop_table("job_matches")
