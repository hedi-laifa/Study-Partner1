"""add_evaluation_evidence_progress

Revision ID: 746a4f260c44
Revises: e666c101aa0a
Create Date: 2026-11-06 02:31:29.286148

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '746a4f260c44'
down_revision: Union[str, Sequence[str], None] = 'e666c101aa0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("verdict", sa.String(50), nullable=False),
        sa.Column("rubric_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False, server_default="Medium"),
    )

    op.create_table(
        "learning_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evaluation_id", sa.Integer(), sa.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("conditions", sa.String(255), nullable=True),
    )
    op.create_index("ix_learning_evidence_concept_id", "learning_evidence", ["concept_id"])
    op.create_index("ix_learning_evidence_evaluation_id", "learning_evidence", ["evaluation_id"])

    op.create_table(
        "concept_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="not-enough-evidence"),
        sa.Column("estimate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("concept_progress")
    op.drop_index("ix_learning_evidence_evaluation_id", "learning_evidence")
    op.drop_index("ix_learning_evidence_concept_id", "learning_evidence")
    op.drop_table("learning_evidence")
    op.drop_table("evaluations")
