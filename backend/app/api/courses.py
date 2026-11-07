from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseCreate, CourseResponse
from app.services.user_seeder import seed_new_user_workspace

router = APIRouter(prefix="/courses", tags=["courses"])


def _current_user_id(x_user_id: int | None = Header(None)) -> int:
    return x_user_id or 1


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    body: CourseCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    course = Course(user_id=user_id, **body.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("", response_model=list[CourseResponse])
def list_courses(
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    user = db.get(User, user_id)
    if user:
        seed_new_user_workspace(db, user)
    return db.query(Course).filter(Course.user_id == user_id).all()


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    course = None
    if course_id.isdigit():
        cid = int(course_id)
        course = db.query(Course).filter(Course.id == cid, Course.user_id == user_id).first()
        if not course:
            course = db.get(Course, cid)

    if not course:
        title_search = course_id.replace("-", " ").strip()
        course = db.query(Course).filter(Course.user_id == user_id, Course.title.ilike(f"%{title_search}%")).first()

    if not course:
        course = db.query(Course).filter(Course.user_id == user_id).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    return course
