from datetime import date

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.dashboard_service import (
    ActivityDay,
    ConceptSummary,
    DashboardData,
    ExamSummary,
    RoadmapSummary,
    StreakInfo,
    get_activity_log,
    get_dashboard,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _uid(x_user_id: int = Header(...)) -> int:
    return x_user_id


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int


class ConceptResponse(BaseModel):
    concept_id: int
    name: str
    status: str
    estimate: float


class RoadmapResponse(BaseModel):
    user_roadmap_id: int
    roadmap_id: int
    role: str
    total_nodes: int
    completed_nodes: int
    progress_pct: float


class ExamResponse(BaseModel):
    attempt_id: int
    exam_title: str
    submitted_at: str
    total_questions: int
    correct: int
    score_pct: float


class DashboardResponse(BaseModel):
    streak: StreakResponse
    concepts: list[ConceptResponse]
    roadmaps: list[RoadmapResponse]
    recent_exams: list[ExamResponse]


class ActivityDayResponse(BaseModel):
    date: date
    activities_completed: int
    questions_answered: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=DashboardResponse)
def dashboard(
    timezone: str = Query(default="UTC", alias="tz"),
    db: Session = Depends(get_db),
    user_id: int = Depends(_uid),
):
    data: DashboardData = get_dashboard(db, user_id, tz_name=timezone)

    return DashboardResponse(
        streak=StreakResponse(
            current_streak=data.streak.current_streak,
            longest_streak=data.streak.longest_streak,
        ),
        concepts=[
            ConceptResponse(
                concept_id=c.concept_id,
                name=c.name,
                status=c.status,
                estimate=c.estimate,
            )
            for c in data.concepts
        ],
        roadmaps=[
            RoadmapResponse(
                user_roadmap_id=r.user_roadmap_id,
                roadmap_id=r.roadmap_id,
                role=r.role,
                total_nodes=r.total_nodes,
                completed_nodes=r.completed_nodes,
                progress_pct=r.progress_pct,
            )
            for r in data.roadmaps
        ],
        recent_exams=[
            ExamResponse(
                attempt_id=e.attempt_id,
                exam_title=e.exam_title,
                submitted_at=e.submitted_at.isoformat(),
                total_questions=e.total_questions,
                correct=e.correct,
                score_pct=e.score_pct,
            )
            for e in data.recent_exams
        ],
    )


@router.get("/activity", response_model=list[ActivityDayResponse])
def activity_log(
    days: int = Query(default=30, ge=1, le=365),
    timezone: str = Query(default="UTC", alias="tz"),
    db: Session = Depends(get_db),
    user_id: int = Depends(_uid),
):
    rows = get_activity_log(db, user_id, days=days, tz_name=timezone)
    return [
        ActivityDayResponse(
            date=r.date,
            activities_completed=r.activities_completed,
            questions_answered=r.questions_answered,
        )
        for r in rows
    ]
