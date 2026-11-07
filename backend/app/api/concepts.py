from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.concept import Concept
from app.models.course import Course

router = APIRouter(prefix="/courses", tags=["concepts"])


def _current_user_id(x_user_id: int = Header(...)) -> int:
    return x_user_id


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
    user_id: int = Depends(_current_user_id),
):
    cid = int(course_id) if course_id.isdigit() else None
    course = None
    if cid:
        course = db.get(Course, cid)
    if not course:
        title_search = course_id.replace("-", " ").strip()
        course = db.query(Course).filter(Course.title.ilike(f"%{title_search}%")).first()

    if not course:
        return []
    return db.query(Concept).filter(Concept.course_id == course.id).all()
