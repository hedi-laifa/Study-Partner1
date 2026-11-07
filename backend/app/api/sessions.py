from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course
from app.models.study_session import StudySession
from app.schemas.session import ActivityResponse, NextActivityRequest, SessionCreate, SessionResponse
from app.services.orchestrator import advance_session, init_session

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _current_user_id(x_user_id: int = Header(...)) -> int:
    return x_user_id


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    body: SessionCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    course = db.query(Course).filter(Course.id == body.course_id, Course.user_id == user_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    session = init_session(db, body.course_id, body.goal, body.knowledge_mode)
    return session


@router.post("/{session_id}/next", response_model=ActivityResponse)
def next_activity(
    session_id: int,
    body: NextActivityRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    session = (
        db.query(StudySession)
        .join(Course)
        .filter(StudySession.id == session_id, Course.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session is not active")
    activity = advance_session(db, session, body.answer, body.hint_count)
    return activity
