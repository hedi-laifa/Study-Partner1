"""add_practice_exams

Revision ID: 6bb8e1bed05e
Revises: 45dc5482084d
Create Date: 2026-11-06 02:35:16.348434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bb8e1bed05e'
down_revision: Union[str, Sequence[str], None] = '45dc5482084d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "practice_exams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("status", sa.String(50), nullable=False, server_default="ready"),
    )
    op.create_index("ix_practice_exams_course_id", "practice_exams", ["course_id"])

    op.create_table(
        "exam_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("practice_exams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", sa.String(50), nullable=False, server_default="short-answer"),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_exam_questions_exam_id", "exam_questions", ["exam_id"])

    op.create_table(
        "exam_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("practice_exams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="in-progress"),
    )
    op.create_index("ix_exam_attempts_exam_id", "exam_attempts", ["exam_id"])
    op.create_index("ix_exam_attempts_user_id", "exam_attempts", ["user_id"])

    op.create_table(
        "exam_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("exam_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verdict", sa.String(50), nullable=True),
        sa.Column("rubric_score", sa.Float(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
    )
    op.create_index("ix_exam_answers_attempt_id", "exam_answers", ["attempt_id"])


def downgrade() -> None:
    op.drop_index("ix_exam_answers_attempt_id", "exam_answers")
    op.drop_table("exam_answers")
    op.drop_index("ix_exam_attempts_user_id", "exam_attempts")
    op.drop_index("ix_exam_attempts_exam_id", "exam_attempts")
    op.drop_table("exam_attempts")
    op.drop_index("ix_exam_questions_exam_id", "exam_questions")
    op.drop_table("exam_questions")
    op.drop_index("ix_practice_exams_course_id", "practice_exams")
    op.drop_table("practice_exams")
