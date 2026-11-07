from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="generated")

    nodes: Mapped[list["RoadmapNode"]] = relationship(back_populates="roadmap", cascade="all, delete-orphan")
    user_roadmaps: Mapped[list["UserRoadmap"]] = relationship(back_populates="roadmap", cascade="all, delete-orphan")
