from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("practice_exams.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="short-answer")
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON-encoded list of strings for multiple-choice; NULL for short-answer
    options: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam: Mapped["PracticeExam"] = relationship(back_populates="questions")
    answers: Mapped[list["ExamAnswer"]] = relationship(back_populates="question", cascade="all, delete-orphan")
