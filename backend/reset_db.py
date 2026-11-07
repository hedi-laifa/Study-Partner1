"""
Reset script: deletes ALL users and their associated data from the database.
Roadmaps and their nodes (shared content) are preserved.

Usage:
    cd backend
    python reset_db.py
"""

from sqlalchemy import text
from app.core.database import engine


def reset():
    with engine.connect() as conn:
        # Roll back any pending transaction first
        try:
            conn.rollback()
        except Exception:
            pass

        # Delete all users — foreign keys with CASCADE will remove everything linked to them
        conn.execute(text("DELETE FROM users;"))

        # Reset sequences so IDs start from 1 again
        sequences = [
            "users_id_seq",
            "courses_id_seq",
            "concepts_id_seq",
            "documents_id_seq",
            "chunks_id_seq",
            "study_sessions_id_seq",
            "activities_id_seq",
            "attempts_id_seq",
            "evaluations_id_seq",
            "practice_exams_id_seq",
            "exam_questions_id_seq",
            "exam_attempts_id_seq",
            "exam_answers_id_seq",
            "user_roadmaps_id_seq",
            "roadmap_node_progress_id_seq",
            "concept_progress_id_seq",
        ]
        for seq in sequences:
            try:
                conn.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1;"))
            except Exception:
                conn.rollback()

        conn.commit()

    print("Done. All users deleted. You can now register fresh accounts.")


if __name__ == "__main__":
    reset()
