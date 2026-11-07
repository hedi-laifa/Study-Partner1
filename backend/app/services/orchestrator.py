from sqlalchemy.orm import Session as DBSession

from app.models.activity import Activity
from app.models.attempt import Attempt
from app.models.concept import Concept
from app.models.study_session import StudySession
from app.services.llm_service import generate_tutor_response
from app.services.retriever import retrieve_chunks

DIAGNOSTIC_PROMPT_TEMPLATE = (
    "You are opening a study session. The student's goal is: \"{goal}\".\n"
    "Based on the course material provided, generate ONE open-ended diagnostic question "
    "that reveals what the student already understands about the core concepts. "
    "Return only the question, nothing else."
)

FOLLOWUP_PROMPT_TEMPLATE = (
    "The student answered: \"{answer}\".\n"
    "Based on the course material and their response, generate ONE follow-up question "
    "that deepens their understanding or addresses a gap. "
    "Return only the question, nothing else."
)


def _first_concept(db: DBSession, course_id: int) -> Concept | None:
    return db.query(Concept).filter(Concept.course_id == course_id).first()


def init_session(db: DBSession, course_id: int, goal: str | None, knowledge_mode: str) -> StudySession:
    """Create a StudySession and its first diagnostic Activity."""
    session = StudySession(
        course_id=course_id,
        goal=goal or "General study",
        status="active",
        knowledge_mode=knowledge_mode,
    )
    db.add(session)
    db.flush()

    # Retrieve relevant chunks to ground the diagnostic question
    chunks = retrieve_chunks(db, course_id, session.goal)
    context = [c.text for c in chunks]

    prompt_input = DIAGNOSTIC_PROMPT_TEMPLATE.format(goal=session.goal)
    question = generate_tutor_response(prompt_input, context)

    concept = _first_concept(db, course_id)
    activity = Activity(
        session_id=session.id,
        concept_id=concept.id if concept else None,
        type="diagnostic",
        difficulty="medium",
        prompt=question,
        mode=knowledge_mode,
    )
    db.add(activity)
    db.commit()
    db.refresh(session)
    return session


def advance_session(db: DBSession, session: StudySession, answer: str, hint_count: int) -> Activity:
    """Record an Attempt for the latest activity and generate the next one."""
    latest = (
        db.query(Activity)
        .filter(Activity.session_id == session.id)
        .order_by(Activity.id.desc())
        .first()
    )
    if not latest:
        raise ValueError("Session has no activities")

    # Persist the attempt
    attempt = Attempt(activity_id=latest.id, answer=answer, hint_count=hint_count)
    db.add(attempt)
    db.flush()

    # Retrieve context for the follow-up
    chunks = retrieve_chunks(db, session.course_id, answer)
    context = [c.text for c in chunks]

    prompt_input = FOLLOWUP_PROMPT_TEMPLATE.format(answer=answer)
    next_question = generate_tutor_response(prompt_input, context)

    next_activity = Activity(
        session_id=session.id,
        concept_id=latest.concept_id,
        type="follow-up",
        difficulty=latest.difficulty,
        prompt=next_question,
        mode=latest.mode,
    )
    db.add(next_activity)
    db.commit()
    db.refresh(next_activity)
    return next_activity
