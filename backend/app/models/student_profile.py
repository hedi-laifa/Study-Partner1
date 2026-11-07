from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    field_of_study: Mapped[str | None] = mapped_column(String(255))
    domain_type: Mapped[str | None] = mapped_column(String(100))
    level: Mapped[str | None] = mapped_column(String(50))
    language: Mapped[str] = mapped_column(String(10), default="en")

    user: Mapped["User"] = relationship(back_populates="profile")
