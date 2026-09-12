"""add interview response mode

Revision ID: 20260913_07
Revises: 20260905_06
Create Date: 2026-09-13
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260913_07"
down_revision: str | None = "20260905_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "interview_sessions",
        sa.Column("response_mode", sa.String(length=20), server_default="text", nullable=False),
    )
    op.create_check_constraint(
        "ck_interview_sessions_response_mode",
        "interview_sessions",
        "response_mode IN ('text', 'video')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_interview_sessions_response_mode",
        "interview_sessions",
        type_="check",
    )
    op.drop_column("interview_sessions", "response_mode")
