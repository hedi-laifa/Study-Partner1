"""initial_relational_tables

Revision ID: 04391616d87d
Revises: 
Create Date: 2026-11-06 02:20:24.570446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04391616d87d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "student_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("field_of_study", sa.String(255), nullable=True),
        sa.Column("domain_type", sa.String(100), nullable=True),
        sa.Column("level", sa.String(50), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
    )

    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("domain_type", sa.String(100), nullable=True),
    )
    op.create_index("ix_courses_user_id", "courses", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_courses_user_id", "courses")
    op.drop_table("courses")
    op.drop_table("student_profiles")
    op.drop_index("ix_users_email", "users")
    op.drop_table("users")
