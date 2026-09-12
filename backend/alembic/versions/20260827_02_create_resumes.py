"""create resumes table

Revision ID: 20260827_02
Revises: 20260827_01
Create Date: 2026-08-27
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260827_02"
down_revision: str | None = "20260827_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=64), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("parsed_text", sa.Text(), nullable=False),
        sa.Column("structured_data", sa.JSON(), nullable=False),
        sa.Column("parsing_status", sa.String(length=20), nullable=False),
        sa.Column("parsing_error", sa.String(length=255), nullable=True),
        sa.CheckConstraint("parsing_status IN ('parsed', 'failed')", name="ck_resumes_parsing_status"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index(op.f("ix_resumes_user_id"), "resumes", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_resumes_user_id"), table_name="resumes")
    op.drop_table("resumes")
