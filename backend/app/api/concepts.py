from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.concept import Concept
from app.models.course import Course
from app.models.user import User

router = APIRouter(prefix="/courses", tags=["concepts"])


class ConceptResponse(BaseModel):
    id: int
    course_id: int
    name: str
    description: str | None
    domain_type: str | None

    model_config = {"from_attributes": True}


@router.get("/{course_id}/concepts", response_model=list[ConceptResponse])
def list_concepts(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = int(course_id) if course_id.isdigit() else None
    course = None
    if cid:
        course = db.query(Course).filter(
            Course.id == cid, Course.user_id == current_user.id
        ).first()
    if not course:
        title_search = course_id.replace("-", " ").strip()
        course = db.query(Course).filter(
            Course.user_id == current_user.id, Course.title.ilike(f"%{title_search}%")
        ).first()

    if not course:
        return []
    return db.query(Concept).filter(Concept.course_id == course.id).all()
