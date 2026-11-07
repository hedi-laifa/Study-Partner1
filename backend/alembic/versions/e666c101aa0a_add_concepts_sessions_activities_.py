"""add_concepts_sessions_activities_attempts

Revision ID: e666c101aa0a
Revises: 89f05497683b
Create Date: 2026-11-06 02:29:26.743435

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e666c101aa0a'
down_revision: Union[str, Sequence[str], None] = '89f05497683b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "concepts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("domain_type", sa.String(100), nullable=True),
    )
    op.create_index("ix_concepts_course_id", "concepts", ["course_id"])

    op.create_table(
        "study_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("knowledge_mode", sa.String(50), nullable=False, server_default="course-grounded"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_study_sessions_course_id", "study_sessions", ["course_id"])

    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.String(50), nullable=False, server_default="diagnostic"),
        sa.Column("difficulty", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(50), nullable=False, server_default="course-grounded"),
    )
    op.create_index("ix_activities_session_id", "activities", ["session_id"])

    op.create_table(
        "attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hint_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_attempts_activity_id", "attempts", ["activity_id"])


def downgrade() -> None:
    op.drop_index("ix_attempts_activity_id", "attempts")
    op.drop_table("attempts")
    op.drop_index("ix_activities_session_id", "activities")
    op.drop_table("activities")
    op.drop_index("ix_study_sessions_course_id", "study_sessions")
    op.drop_table("study_sessions")
    op.drop_index("ix_concepts_course_id", "concepts")
    op.drop_table("concepts")
