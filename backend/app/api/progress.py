from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.activity import Activity
from app.models.attempt import Attempt
from app.models.concept import Concept
from app.models.concept_progress import ConceptProgress
from app.models.course import Course
from app.models.daily_activity import DailyActivity
from app.models.evaluation import Evaluation
from app.models.study_session import StudySession
from app.models.user import User

router = APIRouter(prefix="/progress", tags=["progress"])


class ProgressAttemptSchema(BaseModel):
    id: str
    date: str
    verdict: str
    answer: str
    evidence: str
    confidence: str


class ProgressConceptSchema(BaseModel):
    id: str
    name: str
    course: str
    courseId: str
    status: str
    evidence: str
    progress: int
    reason: str | None = None
    practiceSessionId: str | None = None
    recommendedAction: str
    attempts: list[ProgressAttemptSchema] = []


class ProgressSessionSchema(BaseModel):
    id: str
    title: str
    course: str
    date: str
    duration: str
    outcome: str
    verdict: str
    completed: bool


class ProgressResponse(BaseModel):
    studyMinutes: int
    sessionsCompleted: int
    questionsAnswered: int
    concepts: list[ProgressConceptSchema]
    recentSessions: list[ProgressSessionSchema]
    weeklyActivity: list[dict]


def _map_status(raw_status: str, estimate: float) -> str:
    s = (raw_status or "").lower()
    if "good" in s or estimate >= 0.75:
        return "Good evidence"
    if "developing" in s or (0.4 <= estimate < 0.75):
        return "Developing"
    if "practice" in s or (0 < estimate < 0.4):
        return "Needs practice"
    return "Not enough evidence"


@router.get("", response_model=ProgressResponse)
def get_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    courses = db.query(Course).filter(Course.user_id == current_user.id).all()
    course_map = {c.id: c for c in courses}
    course_ids = list(course_map.keys())

    daily_rows = (
        db.query(DailyActivity)
        .filter(DailyActivity.user_id == current_user.id)
        .order_by(DailyActivity.date.desc())
        .limit(30)
        .all()
    )
    total_questions = sum(d.questions_answered for d in daily_rows)
    total_activities = sum(d.activities_completed for d in daily_rows)

    sessions = []
    if course_ids:
        sessions = (
            db.query(StudySession)
            .filter(StudySession.course_id.in_(course_ids))
            .order_by(StudySession.created_at.desc())
            .limit(10)
            .all()
        )

    completed_sessions_count = sum(1 for s in sessions if s.status == "completed")
    total_attempts_count = 0
    if course_ids:
        total_attempts_count = (
            db.query(Attempt)
            .join(Activity, Attempt.activity_id == Activity.id)
            .join(StudySession, Activity.session_id == StudySession.id)
            .filter(StudySession.course_id.in_(course_ids))
            .count()
        )

    questions_count = max(total_questions, total_attempts_count)
    study_minutes = max(total_activities * 15, len(sessions) * 20, 25 if questions_count > 0 else 0)

    concepts_list: list[ProgressConceptSchema] = []
    if course_ids:
        all_concepts = db.query(Concept).filter(Concept.course_id.in_(course_ids)).all()
        for cp in all_concepts:
            progress_rec = db.query(ConceptProgress).filter(ConceptProgress.concept_id == cp.id).first()
            raw_status = progress_rec.status if progress_rec else "not-enough-evidence"
            estimate = progress_rec.estimate if progress_rec else 0.0

            status_str = _map_status(raw_status, estimate)
            progress_pct = int(estimate * 100) if estimate else 0
            course_obj = course_map.get(cp.course_id)
            course_title = course_obj.title if course_obj else "General"

            linked_activities = db.query(Activity).filter(Activity.concept_id == cp.id).all()
            act_ids = [a.id for a in linked_activities]
            attempts_schema: list[ProgressAttemptSchema] = []
            if act_ids:
                linked_attempts = (
                    db.query(Attempt)
                    .filter(Attempt.activity_id.in_(act_ids))
                    .order_by(Attempt.created_at.desc())
                    .limit(3)
                    .all()
                )
                for at in linked_attempts:
                    ev = at.evaluation
                    verdict = ev.verdict if ev else "Needs review"
                    confidence = ev.confidence if ev else "Medium"
                    feedback = ev.feedback if ev else "Recorded attempt"
                    attempts_schema.append(
                        ProgressAttemptSchema(
                            id=str(at.id),
                            date=at.created_at.strftime("%b %d") if at.created_at else "Recent",
                            verdict=verdict if verdict in ("Correct", "Partially correct") else "Needs review",
                            answer=at.answer,
                            evidence=feedback,
                            confidence=confidence if confidence in ("High", "Medium", "Low") else "Medium",
                        )
                    )

            reason_str = None
            if status_str == "Needs practice":
                reason_str = "Recent attempt showed gaps in explanation."
            elif status_str == "Not enough evidence":
                reason_str = "No recent answered questions for this concept."

            recommended = (
                "Review the fundamentals and test with structured exercises."
                if status_str in ("Needs practice", "Not enough evidence")
                else "Continue challenging your knowledge with higher difficulty questions."
            )

            concepts_list.append(
                ProgressConceptSchema(
                    id=str(cp.id),
                    name=cp.name,
                    course=course_title,
                    courseId=str(cp.course_id),
                    status=status_str,
                    evidence=f"{len(attempts_schema)} recent verified answers" if attempts_schema else "No responses recorded yet",
                    progress=progress_pct,
                    reason=reason_str,
                    practiceSessionId=str(sessions[0].id) if sessions else None,
                    recommendedAction=recommended,
                    attempts=attempts_schema,
                )
            )

    recent_sessions_schema: list[ProgressSessionSchema] = []
    for s in sessions:
        c_obj = course_map.get(s.course_id)
        c_title = c_obj.title if c_obj else "Study Session"
        recent_sessions_schema.append(
            ProgressSessionSchema(
                id=str(s.id),
                title=s.goal or f"{c_title} Practice",
                course=c_title,
                date=s.created_at.strftime("%a, %I:%M %p") if s.created_at else "Today",
                duration="20 min",
                outcome=f"Session status: {s.status}",
                verdict="Correct" if s.status == "completed" else "Needs review",
                completed=s.status == "completed",
            )
        )

    today = datetime.now(timezone.utc).date()
    days_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    weekly_activity = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_name = days_map[d.weekday()]
        act_row = next((r for r in daily_rows if r.date == d), None)
        weekly_activity.append({
            "day": day_name,
            "questions": act_row.questions_answered if act_row else 0,
            "sessions": act_row.activities_completed if act_row else 0,
            "minutes": (act_row.activities_completed if act_row else 0) * 15,
        })

    return ProgressResponse(
        studyMinutes=study_minutes,
        sessionsCompleted=completed_sessions_count or len(sessions),
        questionsAnswered=questions_count,
        concepts=concepts_list,
        recentSessions=recent_sessions_schema,
        weeklyActivity=weekly_activity,
    )
