from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False, unique=True)
    verdict: Mapped[str] = mapped_column(String(50), nullable=False)
    rubric_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False, default="Medium")

    attempt: Mapped["Attempt"] = relationship(back_populates="evaluation")
    evidence: Mapped[list["LearningEvidence"]] = relationship(back_populates="evaluation", cascade="all, delete-orphan")
