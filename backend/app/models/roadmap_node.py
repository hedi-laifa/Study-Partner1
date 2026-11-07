from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoadmapNode(Base):
    __tablename__ = "roadmap_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    roadmap_id: Mapped[int] = mapped_column(ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False, index=True)
    # prerequisite is a self-referencing FK to another node in the same roadmap
    prerequisite_id: Mapped[int | None] = mapped_column(ForeignKey("roadmap_nodes.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    roadmap: Mapped["Roadmap"] = relationship(back_populates="nodes")
    prerequisite: Mapped["RoadmapNode | None"] = relationship(remote_side="RoadmapNode.id")
    node_progress: Mapped[list["RoadmapNodeProgress"]] = relationship(back_populates="node", cascade="all, delete-orphan")
