from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PracticeExam(Base):
    __tablename__ = "practice_exams"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    time_limit_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ready")

    course: Mapped["Course"] = relationship()
    questions: Mapped[list["ExamQuestion"]] = relationship(back_populates="exam", cascade="all, delete-orphan")
    attempts: Mapped[list["ExamAttempt"]] = relationship(back_populates="exam", cascade="all, delete-orphan")
