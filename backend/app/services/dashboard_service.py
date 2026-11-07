from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session as DBSession

from app.models.concept_progress import ConceptProgress
from app.models.daily_activity import DailyActivity
from app.models.exam_attempt import ExamAttempt
from app.models.exam_answer import ExamAnswer
from app.models.user_roadmap import UserRoadmap
from app.models.roadmap_node_progress import RoadmapNodeProgress


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------

@dataclass
class ConceptSummary:
    concept_id: int
    name: str
    status: str
    estimate: float


@dataclass
class RoadmapSummary:
    user_roadmap_id: int
    roadmap_id: int
    role: str
    total_nodes: int
    completed_nodes: int
    progress_pct: float


@dataclass
class ExamSummary:
    attempt_id: int
    exam_title: str
    submitted_at: datetime
    total_questions: int
    correct: int
    score_pct: float


@dataclass
class StreakInfo:
    current_streak: int
    longest_streak: int


@dataclass
class DashboardData:
    concepts: list[ConceptSummary] = field(default_factory=list)
    roadmaps: list[RoadmapSummary] = field(default_factory=list)
    recent_exams: list[ExamSummary] = field(default_factory=list)
    streak: StreakInfo = field(default_factory=lambda: StreakInfo(0, 0))


@dataclass
class ActivityDay:
    date: date
    activities_completed: int
    questions_answered: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today_in_tz(tz_name: str) -> date:
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, KeyError):
        tz = timezone.utc
    return datetime.now(tz).date()


def _compute_streaks(sorted_dates: list[date], today: date) -> StreakInfo:
    """
    sorted_dates: ascending list of distinct active days.
    An active day counts toward the current streak only if the chain
    reaches today or yesterday (allows the user to still be active today).
    """
    if not sorted_dates:
        return StreakInfo(0, 0)

    # Longest streak
    longest = current_run = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 1

    # Current streak — walk backwards from today
    day_set = set(sorted_dates)
    current = 0
    cursor = today
    while cursor in day_set:
        current += 1
        cursor -= timedelta(days=1)
    # Also accept yesterday as the start (user hasn't studied yet today)
    if current == 0:
        cursor = today - timedelta(days=1)
        while cursor in day_set:
            current += 1
            cursor -= timedelta(days=1)

    return StreakInfo(current_streak=current, longest_streak=longest)


# ---------------------------------------------------------------------------
# Aggregation queries
# ---------------------------------------------------------------------------

def _concept_summaries(db: DBSession, user_id: int) -> list[ConceptSummary]:
    from app.models.concept import Concept
    from app.models.course import Course

    rows = (
        db.query(ConceptProgress, Concept)
        .join(Concept, ConceptProgress.concept_id == Concept.id)
        .join(Course, Concept.course_id == Course.id)
        .filter(Course.user_id == user_id)
        .all()
    )
    return [
        ConceptSummary(
            concept_id=cp.concept_id,
            name=c.name,
            status=cp.status,
            estimate=cp.estimate,
        )
        for cp, c in rows
    ]


def _roadmap_summaries(db: DBSession, user_id: int) -> list[RoadmapSummary]:
    from app.models.roadmap import Roadmap
    from app.models.roadmap_node import RoadmapNode

    user_roadmaps = (
        db.query(UserRoadmap)
        .filter(UserRoadmap.user_id == user_id)
        .all()
    )
    summaries: list[RoadmapSummary] = []
    for ur in user_roadmaps:
        roadmap: Roadmap = ur.roadmap
        total = db.query(RoadmapNode).filter(RoadmapNode.roadmap_id == roadmap.id).count()
        completed = (
            db.query(RoadmapNodeProgress)
            .filter(
                RoadmapNodeProgress.user_roadmap_id == ur.id,
                RoadmapNodeProgress.status == "completed",
            )
            .count()
        )
        summaries.append(RoadmapSummary(
            user_roadmap_id=ur.id,
            roadmap_id=roadmap.id,
            role=roadmap.role,
            total_nodes=total,
            completed_nodes=completed,
            progress_pct=round(completed / total * 100, 1) if total else 0.0,
        ))
    return summaries


def _recent_exam_summaries(db: DBSession, user_id: int, limit: int = 5) -> list[ExamSummary]:
    attempts = (
        db.query(ExamAttempt)
        .filter(ExamAttempt.user_id == user_id, ExamAttempt.status == "submitted")
        .order_by(ExamAttempt.submitted_at.desc())
        .limit(limit)
        .all()
    )
    summaries: list[ExamSummary] = []
    for attempt in attempts:
        total = len(attempt.answers)
        correct = sum(
            1 for a in attempt.answers
            if a.verdict in ("Correct", "Partially correct")
        )
        summaries.append(ExamSummary(
            attempt_id=attempt.id,
            exam_title=attempt.exam.title,
            submitted_at=attempt.submitted_at,
            total_questions=total,
            correct=correct,
            score_pct=round(correct / total * 100, 1) if total else 0.0,
        ))
    return summaries


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_dashboard(db: DBSession, user_id: int, tz_name: str = "UTC") -> DashboardData:
    today = _today_in_tz(tz_name)

    active_dates = sorted(
        row.date
        for row in db.query(DailyActivity).filter(DailyActivity.user_id == user_id).all()
    )
    streak = _compute_streaks(active_dates, today)

    return DashboardData(
        concepts=_concept_summaries(db, user_id),
        roadmaps=_roadmap_summaries(db, user_id),
        recent_exams=_recent_exam_summaries(db, user_id),
        streak=streak,
    )


def get_activity_log(
    db: DBSession,
    user_id: int,
    days: int = 30,
    tz_name: str = "UTC",
) -> list[ActivityDay]:
    today = _today_in_tz(tz_name)
    since = today - timedelta(days=days - 1)

    rows = (
        db.query(DailyActivity)
        .filter(DailyActivity.user_id == user_id, DailyActivity.date >= since)
        .order_by(DailyActivity.date)
        .all()
    )
    return [ActivityDay(date=r.date, activities_completed=r.activities_completed, questions_answered=r.questions_answered) for r in rows]
