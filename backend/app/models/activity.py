from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="diagnostic")
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="course-grounded")

    session: Mapped["StudySession"] = relationship(back_populates="activities")
    concept: Mapped["Concept | None"] = relationship(back_populates="activities")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="activity", cascade="all, delete-orphan")
