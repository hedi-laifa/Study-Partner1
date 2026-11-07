"""add_roadmaps

Revision ID: 45dc5482084d
Revises: 746a4f260c44
Create Date: 2026-11-06 02:33:15.203950

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45dc5482084d'
down_revision: Union[str, Sequence[str], None] = '746a4f260c44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roadmaps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="generated"),
    )

    op.create_table(
        "roadmap_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("roadmap_id", sa.Integer(), sa.ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prerequisite_id", sa.Integer(), sa.ForeignKey("roadmap_nodes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("optional", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_roadmap_nodes_roadmap_id", "roadmap_nodes", ["roadmap_id"])

    op.create_table(
        "user_roadmaps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("roadmap_id", sa.Integer(), sa.ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_roadmaps_user_id", "user_roadmaps", ["user_id"])

    op.create_table(
        "roadmap_node_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_roadmap_id", sa.Integer(), sa.ForeignKey("user_roadmaps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_id", sa.Integer(), sa.ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="not-started"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_roadmap_node_progress_user_roadmap_id", "roadmap_node_progress", ["user_roadmap_id"])


def downgrade() -> None:
    op.drop_index("ix_roadmap_node_progress_user_roadmap_id", "roadmap_node_progress")
    op.drop_table("roadmap_node_progress")
    op.drop_index("ix_user_roadmaps_user_id", "user_roadmaps")
    op.drop_table("user_roadmaps")
    op.drop_index("ix_roadmap_nodes_roadmap_id", "roadmap_nodes")
    op.drop_table("roadmap_nodes")
    op.drop_table("roadmaps")
