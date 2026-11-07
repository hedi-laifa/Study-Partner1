import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.course import Course
from app.models.exam_answer import ExamAnswer
from app.models.exam_attempt import ExamAttempt
from app.models.exam_question import ExamQuestion
from app.models.practice_exam import PracticeExam
from app.models.user import User
from app.services.exam_service import assert_within_deadline, bulk_assess_attempt, generate_exam_questions

router = APIRouter(tags=["exams"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ExamCreate(BaseModel):
    course_id: int
    title: str
    time_limit_minutes: int = Field(default=30, ge=5, le=180)
    question_count: int = Field(default=10, ge=3, le=40)
    concept_names: list[str] = Field(default_factory=list)


class ExamQuestionResponse(BaseModel):
    id: int
    type: str
    prompt: str
    options: list[str] | None
    order: int

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_question(cls, q: ExamQuestion) -> "ExamQuestionResponse":
        return cls(
            id=q.id,
            type=q.type,
            prompt=q.prompt,
            options=json.loads(q.options) if q.options else None,
            order=q.order,
        )


class ExamResponse(BaseModel):
    id: int
    course_id: int
    title: str
    time_limit_minutes: int
    question_count: int
    status: str

    model_config = {"from_attributes": True}


class StartAttemptResponse(BaseModel):
    attempt_id: int
    deadline_at: datetime
    questions: list[ExamQuestionResponse]


class AutosaveRequest(BaseModel):
    answer_text: str


class AnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_text: str
    saved_at: datetime

    model_config = {"from_attributes": True}


class ExamResultAnswer(BaseModel):
    question_id: int
    prompt: str
    answer_text: str
    correct_answer: str | None = None
    verdict: str | None = None
    rubric_score: float | None = None
    feedback: str | None = None


class ExamResultResponse(BaseModel):
    attempt_id: int
    submitted_at: datetime
    exam_id: int | None = None
    title: str | None = None
    course: str | None = None
    answers: list[ExamResultAnswer]


class SubmitExamAnswersBody(BaseModel):
    answers: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Helper — always scoped to current user
# ---------------------------------------------------------------------------

def _find_exam_for_user(db: Session, exam_id: str, user_id: int) -> PracticeExam | None:
    """Return a PracticeExam belonging to this user, or None."""
    if exam_id.isdigit():
        exam = (
            db.query(PracticeExam)
            .join(Course)
            .filter(PracticeExam.id == int(exam_id), Course.user_id == user_id)
            .first()
        )
        if exam:
            return exam

    title_search = exam_id.replace("-", " ").strip()
    return (
        db.query(PracticeExam)
        .join(Course)
        .filter(Course.user_id == user_id, PracticeExam.title.ilike(f"%{title_search}%"))
        .first()
    )


def _get_attempt_for_user(db: Session, attempt_id: int, user_id: int) -> ExamAttempt:
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.id == attempt_id, ExamAttempt.user_id == user_id
    ).first()
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    return attempt


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam(
    body: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(
        Course.id == body.course_id, Course.user_id == current_user.id
    ).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    exam = PracticeExam(
        course_id=body.course_id,
        title=body.title,
        time_limit_minutes=body.time_limit_minutes,
        question_count=body.question_count,
        status="generating",
    )
    db.add(exam)
    db.flush()

    concept_names = body.concept_names or [course.subject or course.title]
    try:
        generate_exam_questions(db, exam, concept_names)
        exam.status = "ready"
    except Exception as exc:
        exam.status = "error"
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    db.commit()
    db.refresh(exam)
    return exam


@router.post("/exams/{exam_id}/start", response_model=StartAttemptResponse, status_code=status.HTTP_201_CREATED)
def start_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exam = _find_exam_for_user(db, exam_id, current_user.id)
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")

    if exam.status != "ready":
        exam.status = "ready"
        db.commit()

    now = datetime.now(timezone.utc)
    attempt = ExamAttempt(
        exam_id=exam.id,
        user_id=current_user.id,
        started_at=now,
        deadline_at=now + timedelta(minutes=exam.time_limit_minutes),
        status="in-progress",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    questions = (
        db.query(ExamQuestion)
        .filter(ExamQuestion.exam_id == exam.id)
        .order_by(ExamQuestion.order)
        .all()
    )

    return StartAttemptResponse(
        attempt_id=attempt.id,
        deadline_at=attempt.deadline_at,
        questions=[ExamQuestionResponse.from_orm_question(q) for q in questions],
    )


@router.patch("/exam-attempts/{attempt_id}/questions/{question_id}/autosave", response_model=AnswerResponse)
def autosave_answer(
    attempt_id: int,
    question_id: int,
    body: AutosaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _get_attempt_for_user(db, attempt_id, current_user.id)
    assert_within_deadline(attempt)

    answer = db.query(ExamAnswer).filter(
        ExamAnswer.attempt_id == attempt_id, ExamAnswer.question_id == question_id
    ).first()
    now = datetime.now(timezone.utc)
    if answer:
        answer.answer_text = body.answer_text
        answer.saved_at = now
    else:
        answer = ExamAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            answer_text=body.answer_text,
            saved_at=now,
        )
        db.add(answer)

    db.commit()
    db.refresh(answer)
    return answer


@router.post("/exams/{exam_id}/submit", response_model=ExamResultResponse)
def submit_exam_with_answers(
    exam_id: str,
    body: SubmitExamAnswersBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exam = _find_exam_for_user(db, exam_id, current_user.id)
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")

    attempt = (
        db.query(ExamAttempt)
        .filter(
            ExamAttempt.exam_id == exam.id,
            ExamAttempt.user_id == current_user.id,
            ExamAttempt.status == "in-progress",
        )
        .order_by(ExamAttempt.started_at.desc())
        .first()
    )
    now = datetime.now(timezone.utc)
    if not attempt:
        attempt = ExamAttempt(
            exam_id=exam.id,
            user_id=current_user.id,
            started_at=now,
            deadline_at=now + timedelta(minutes=exam.time_limit_minutes),
            status="in-progress",
        )
        db.add(attempt)
        db.flush()

    questions = db.query(ExamQuestion).filter(ExamQuestion.exam_id == exam.id).order_by(ExamQuestion.order).all()

    for q in questions:
        ans_text = body.answers.get(str(q.id)) or body.answers.get(f"q_{q.id}") or ""
        existing_ans = db.query(ExamAnswer).filter(
            ExamAnswer.attempt_id == attempt.id, ExamAnswer.question_id == q.id
        ).first()
        if existing_ans:
            existing_ans.answer_text = ans_text
            existing_ans.saved_at = now
        else:
            db.add(ExamAnswer(attempt_id=attempt.id, question_id=q.id, answer_text=ans_text, saved_at=now))
    db.flush()

    bulk_assess_attempt(db, attempt)

    attempt.status = "submitted"
    attempt.submitted_at = now
    db.commit()
    db.refresh(attempt)

    course_obj = db.get(Course, exam.course_id) if exam.course_id else None

    return ExamResultResponse(
        attempt_id=attempt.id,
        exam_id=exam.id,
        title=exam.title,
        course=course_obj.title if course_obj else "Practice Course",
        submitted_at=attempt.submitted_at,
        answers=[
            ExamResultAnswer(
                question_id=a.question_id,
                prompt=a.question.prompt if a.question else "Question",
                answer_text=a.answer_text,
                correct_answer=a.question.correct_answer if a.question else None,
                verdict=a.verdict or "Needs review",
                rubric_score=a.rubric_score,
                feedback=a.feedback or (f"Correct answer: {a.question.correct_answer}" if a.question else ""),
            )
            for a in attempt.answers
        ],
    )


@router.post("/exam-attempts/{attempt_id}/submit", response_model=ExamResultResponse)
def submit_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = _get_attempt_for_user(db, attempt_id, current_user.id)
    assert_within_deadline(attempt)

    bulk_assess_attempt(db, attempt)

    attempt.status = "submitted"
    attempt.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(attempt)

    course_obj = db.get(Course, attempt.exam.course_id) if (attempt.exam and attempt.exam.course_id) else None

    return ExamResultResponse(
        attempt_id=attempt.id,
        exam_id=attempt.exam_id,
        title=attempt.exam.title if attempt.exam else "Practice Exam",
        course=course_obj.title if course_obj else "Practice Course",
        submitted_at=attempt.submitted_at,
        answers=[
            ExamResultAnswer(
                question_id=a.question_id,
                prompt=a.question.prompt,
                answer_text=a.answer_text,
                correct_answer=a.question.correct_answer if a.question else None,
                verdict=a.verdict,
                rubric_score=a.rubric_score,
                feedback=a.feedback,
            )
            for a in attempt.answers
        ],
    )


@router.get("/exams", response_model=list[ExamResponse])
def list_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(PracticeExam)
        .join(Course)
        .filter(Course.user_id == current_user.id)
        .all()
    )


@router.get("/exams/{exam_id}", response_model=ExamResponse)
def get_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exam = _find_exam_for_user(db, exam_id, current_user.id)
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return exam


class ExamAttemptSummary(BaseModel):
    id: str
    title: str
    course: str
    date: str
    duration: str
    questionCount: int
    result: str
    score: int
    completed: bool


@router.get("/exam-attempts", response_model=list[ExamAttemptSummary])
def list_exam_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempts = (
        db.query(ExamAttempt)
        .filter(ExamAttempt.user_id == current_user.id)
        .order_by(ExamAttempt.started_at.desc())
        .limit(20)
        .all()
    )

    results: list[ExamAttemptSummary] = []
    for at in attempts:
        total = len(at.answers) or (at.exam.question_count if at.exam else 5)
        correct = sum(1 for a in at.answers if a.verdict in ("Correct", "Partially correct"))
        score_pct = int((correct / total) * 100) if total else 0
        course_obj = db.get(Course, at.exam.course_id) if (at.exam and at.exam.course_id) else None
        results.append(
            ExamAttemptSummary(
                id=str(at.id),
                title=at.exam.title if at.exam else "Practice Exam",
                course=course_obj.title if course_obj else "Practice Course",
                date=at.started_at.strftime("%b %d") if at.started_at else "Recent",
                duration=f"{at.exam.time_limit_minutes if at.exam else 25} min",
                questionCount=total,
                result="Passed" if score_pct >= 70 else "Needs review",
                score=score_pct,
                completed=at.status == "submitted",
            )
        )
    return results


@router.get("/exam-attempts/{attempt_id}/results", response_model=ExamResultResponse)
@router.get("/exams/{attempt_id}/results", response_model=ExamResultResponse)
def get_exam_results(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = None
    if attempt_id.isdigit():
        aid = int(attempt_id)
        attempt = db.query(ExamAttempt).filter(
            ExamAttempt.id == aid, ExamAttempt.user_id == current_user.id
        ).first()
        if not attempt:
            # attempt_id might actually be an exam_id
            attempt = (
                db.query(ExamAttempt)
                .join(PracticeExam, ExamAttempt.exam_id == PracticeExam.id)
                .join(Course, PracticeExam.course_id == Course.id)
                .filter(ExamAttempt.exam_id == aid, Course.user_id == current_user.id)
                .order_by(ExamAttempt.started_at.desc())
                .first()
            )

    if not attempt:
        exam = _find_exam_for_user(db, attempt_id, current_user.id)
        if exam:
            attempt = (
                db.query(ExamAttempt)
                .filter(ExamAttempt.exam_id == exam.id, ExamAttempt.user_id == current_user.id)
                .order_by(ExamAttempt.started_at.desc())
                .first()
            )

    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam results not found")

    course_obj = db.get(Course, attempt.exam.course_id) if (attempt.exam and attempt.exam.course_id) else None

    return ExamResultResponse(
        attempt_id=attempt.id,
        exam_id=attempt.exam_id,
        title=attempt.exam.title if attempt.exam else "Practice Exam",
        course=course_obj.title if course_obj else "Practice Course",
        submitted_at=attempt.submitted_at or attempt.started_at,
        answers=[
            ExamResultAnswer(
                question_id=a.question_id,
                prompt=a.question.prompt if a.question else "Question",
                answer_text=a.answer_text,
                correct_answer=a.question.correct_answer if a.question else None,
                verdict=a.verdict or "Correct",
                rubric_score=a.rubric_score or 1.0,
                feedback=a.feedback or (f"Correct answer: {a.question.correct_answer}" if a.question else ""),
            )
            for a in attempt.answers
        ],
    )
