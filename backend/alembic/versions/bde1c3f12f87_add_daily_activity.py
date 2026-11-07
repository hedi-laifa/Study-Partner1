"""add_daily_activity

Revision ID: bde1c3f12f87
Revises: 6bb8e1bed05e
Create Date: 2026-11-06 02:37:07.366492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bde1c3f12f87'
down_revision: Union[str, Sequence[str], None] = '6bb8e1bed05e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("activities_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("questions_answered", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id", "date", name="uq_daily_activity_user_date"),
    )
    op.create_index("ix_daily_activities_user_id", "daily_activities", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_daily_activities_user_id", "daily_activities")
    op.drop_table("daily_activities")
