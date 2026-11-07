from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from app.models.concept_progress import ConceptProgress
from app.models.learning_evidence import LearningEvidence
from app.models.evaluation import Evaluation

# Score deltas applied to the running estimate per verdict
_VERDICT_DELTA: dict[str, float] = {
    "Correct": +0.20,
    "Partially correct": +0.08,
    "Incorrect": -0.10,
    "Insufficient evidence": 0.0,
}

# Status thresholds (applied after the new estimate is clamped to [0, 1])
def _status_from_estimate(estimate: float) -> str:
    if estimate >= 0.80:
        return "good-evidence"
    if estimate >= 0.50:
        return "developing"
    if estimate >= 0.20:
        return "needs-practice"
    return "not-enough-evidence"


def update_concept_progress(
    db: DBSession,
    evaluation: Evaluation,
    concept_id: int,
) -> ConceptProgress:
    """
    Deterministically update ConceptProgress for a concept using the latest
    Evaluation verdict, then record a LearningEvidence row.
    """
    progress = (
        db.query(ConceptProgress)
        .filter(ConceptProgress.concept_id == concept_id)
        .first()
    )
    if not progress:
        progress = ConceptProgress(concept_id=concept_id, estimate=0.0, status="not-enough-evidence")
        db.add(progress)
        db.flush()

    delta = _VERDICT_DELTA.get(evaluation.verdict, 0.0)
    new_estimate = max(0.0, min(1.0, progress.estimate + delta))
    progress.estimate = new_estimate
    progress.status = _status_from_estimate(new_estimate)
    progress.updated_at = datetime.now(timezone.utc)

    evidence = LearningEvidence(
        concept_id=concept_id,
        evaluation_id=evaluation.id,
        weight=abs(delta) if delta != 0.0 else 0.01,
        conditions=evaluation.verdict,
    )
    db.add(evidence)
    db.flush()
    return progress
