import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.concept import Concept
from app.models.course import Course
from app.models.daily_activity import DailyActivity
from app.models.exam_question import ExamQuestion
from app.models.practice_exam import PracticeExam
from app.models.roadmap import Roadmap
from app.models.roadmap_node_progress import RoadmapNodeProgress
from app.models.study_session import StudySession
from app.models.user import User
from app.models.user_roadmap import UserRoadmap


def seed_new_user_workspace(db: Session, user: User) -> None:
    """
    Initializes a dynamic, personalized learning environment for a new user.
    Creates starter courses, concepts, practice exams, enrolled roadmap, and activity.
    """
    # Check if user already has courses
    existing_courses = db.query(Course).filter(Course.user_id == user.id).all()
    if existing_courses:
        return

    # 1. Create 3 personalized courses for this user
    user_prefix = user.email.split("@")[0].capitalize()

    c1 = Course(
        user_id=user.id,
        title=f"{user_prefix}'s Neural Networks & Deep Learning",
        subject="Deep Learning",
        domain_type="Advanced",
    )
    c2 = Course(
        user_id=user.id,
        title=f"{user_prefix}'s Cloud Architecture & Distributed Systems",
        subject="Computer Science",
        domain_type="Intermediate",
    )
    c3 = Course(
        user_id=user.id,
        title=f"{user_prefix}'s Applied Data Science & Statistics",
        subject="Data Science",
        domain_type="Beginner",
    )
    db.add_all([c1, c2, c3])
    db.flush()

    # 2. Add concepts to these courses
    concepts_c1 = [
        ("Attention Mechanisms", "Query-Key-Value routing in Transformer architectures.", "advanced"),
        ("Residual Connections", "Skip connections mitigating vanishing gradients in deep networks.", "foundational"),
        ("Backpropagation Dynamics", "Chain rule gradient flow through computational graphs.", "foundational"),
    ]
    for name, desc, dtype in concepts_c1:
        db.add(Concept(course_id=c1.id, name=name, description=desc, domain_type=dtype))

    concepts_c2 = [
        ("Microservice Boundaries", "Designing isolated, resilient domain services.", "intermediate"),
        ("Distributed Consensus", "Raft and Paxos state synchronization across clusters.", "advanced"),
        ("Idempotent APIs", "Guaranteed single-execution semantics in distributed queues.", "foundational"),
    ]
    for name, desc, dtype in concepts_c2:
        db.add(Concept(course_id=c2.id, name=name, description=desc, domain_type=dtype))

    concepts_c3 = [
        ("Hypothesis Testing", "Null hypothesis rejection and p-value interpretation.", "foundational"),
        ("Bayesian Inference", "Updating prior belief distributions with observed evidence.", "intermediate"),
    ]
    for name, desc, dtype in concepts_c3:
        db.add(Concept(course_id=c3.id, name=name, description=desc, domain_type=dtype))

    db.flush()

    # 3. Create Practice Exams for this user
    exam1 = PracticeExam(
        course_id=c1.id,
        title=f"{user_prefix} - Transformer Foundations Check",
        time_limit_minutes=25,
        question_count=3,
        status="ready",
    )
    exam2 = PracticeExam(
        course_id=c2.id,
        title=f"{user_prefix} - Distributed Systems Mastery",
        time_limit_minutes=30,
        question_count=2,
        status="ready",
    )
    db.add_all([exam1, exam2])
    db.flush()

    # Add questions with verified correct answers
    q1 = ExamQuestion(
        exam_id=exam1.id,
        order=1,
        type="multiple-choice",
        prompt="In the Scaled Dot-Product Attention equation, why is the dot product divided by the square root of d_k?",
        options=json.dumps([
            "To prevent the dot products from growing large and pushing softmax into regions with small gradients",
            "To normalize the query vector to unit length",
            "To speed up matrix multiplication hardware utilization",
            "To convert negative values into positive scalars",
        ]),
        correct_answer="To prevent the dot products from growing large and pushing softmax into regions with small gradients",
        explanation="Scaling stabilizes softmax gradients for large dimension sizes.",
    )
    q2 = ExamQuestion(
        exam_id=exam1.id,
        order=2,
        type="multiple-choice",
        prompt="What mathematical role do residual connections play in deep neural networks?",
        options=json.dumps([
            "They allow gradients to pass directly through layers without attenuation, solving vanishing gradients",
            "They double the total number of trainable weights at each residual block",
            "They enforce linear separability in the hidden representations",
            "They replace the need for activation functions",
        ]),
        correct_answer="They allow gradients to pass directly through layers without attenuation, solving vanishing gradients",
        explanation="Identity mappings allow unhindered gradient backpropagation.",
    )
    q3 = ExamQuestion(
        exam_id=exam1.id,
        order=3,
        type="short-answer",
        prompt="Explain the difference between self-attention and cross-attention in Transformer sequence-to-sequence models.",
        options=None,
        correct_answer="Self-attention attends within the same sequence, whereas cross-attention uses queries from the decoder and keys/values from the encoder output.",
        explanation="Cross-attention fuses context across different sequences.",
    )
    q4 = ExamQuestion(
        exam_id=exam2.id,
        order=1,
        type="multiple-choice",
        prompt="Which property is guaranteed by an idempotent API endpoint?",
        options=json.dumps([
            "Making multiple identical requests has the same outcome as making a single request",
            "The endpoint responds in constant O(1) time regardless of load",
            "No authentication is needed for read-only requests",
            "Data is replicated to all nodes before acknowledgment",
        ]),
        correct_answer="Making multiple identical requests has the same outcome as making a single request",
        explanation="Idempotency prevents duplicate side-effects during retries.",
    )
    db.add_all([q1, q2, q3, q4])

    # 4. Enroll in a Roadmap
    roadmap = db.query(Roadmap).first()
    if roadmap:
        user_roadmap = UserRoadmap(user_id=user.id, roadmap_id=roadmap.id)
        db.add(user_roadmap)
        db.flush()
        for idx, node in enumerate(roadmap.nodes):
            status = "completed" if idx == 0 else "in-progress" if idx == 1 else "not-started"
            db.add(RoadmapNodeProgress(
                user_roadmap_id=user_roadmap.id,
                node_id=node.id,
                status=status,
            ))

    # 5. Add initial study session and daily activity
    now = datetime.now(timezone.utc)
    db.add(StudySession(
        course_id=c1.id,
        goal="Master core attention mechanisms and residual blocks",
        status="completed",
        knowledge_mode="course-grounded",
        created_at=now,
    ))
    db.add(DailyActivity(
        user_id=user.id,
        date=now.date(),
        activities_completed=2,
        questions_answered=8,
    ))

    db.commit()
