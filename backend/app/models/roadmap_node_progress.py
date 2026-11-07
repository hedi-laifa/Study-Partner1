from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoadmapNodeProgress(Base):
    __tablename__ = "roadmap_node_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_roadmap_id: Mapped[int] = mapped_column(ForeignKey("user_roadmaps.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="not-started")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    user_roadmap: Mapped["UserRoadmap"] = relationship(back_populates="node_progress")
    node: Mapped["RoadmapNode"] = relationship(back_populates="node_progress")
