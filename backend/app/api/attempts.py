from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.activity import Activity
from app.models.attempt import Attempt
from app.models.evaluation import Evaluation
from app.models.study_session import StudySession
from app.models.course import Course
from app.schemas.evaluation import AttemptRequest, EvaluationResponse
from app.services.learning_coach import update_concept_progress
from app.services.llm_service import evaluate_answer
from app.services.retriever import retrieve_chunks

router = APIRouter(prefix="/activities", tags=["attempts"])


def _current_user_id(x_user_id: int = Header(...)) -> int:
    return x_user_id


@router.post("/{activity_id}/attempts", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
def submit_attempt(
    activity_id: int,
    body: AttemptRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    # Verify ownership via activity → session → course → user
    activity = (
        db.query(Activity)
        .join(StudySession, Activity.session_id == StudySession.id)
        .join(Course, StudySession.course_id == Course.id)
        .filter(Activity.id == activity_id, Course.user_id == user_id)
        .first()
    )
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    # Persist attempt
    attempt = Attempt(activity_id=activity.id, answer=body.answer, hint_count=body.hint_count)
    db.add(attempt)
    db.flush()

    # Retrieve relevant context chunks for grounded evaluation
    session = db.get(StudySession, activity.session_id)
    chunks = retrieve_chunks(db, session.course_id, body.answer)
    context = [c.text for c in chunks]

    # LLM evaluation (structured JSON)
    result = evaluate_answer(activity.prompt, body.answer, context)

    evaluation = Evaluation(
        attempt_id=attempt.id,
        verdict=result.verdict,
        rubric_score=result.rubric_score,
        feedback=result.feedback,
        confidence=result.confidence,
    )
    db.add(evaluation)
    db.flush()

    # Update concept progress if activity is linked to a concept
    progress = None
    if activity.concept_id:
        progress = update_concept_progress(db, evaluation, activity.concept_id)

    db.commit()
    db.refresh(evaluation)

    return EvaluationResponse(
        id=evaluation.id,
        attempt_id=evaluation.attempt_id,
        verdict=evaluation.verdict,
        rubric_score=evaluation.rubric_score,
        feedback=evaluation.feedback,
        confidence=evaluation.confidence,
        concept_progress_status=progress.status if progress else None,
        concept_progress_estimate=progress.estimate if progress else None,
    )
