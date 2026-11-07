from pydantic import BaseModel


class AttemptRequest(BaseModel):
    answer: str
    hint_count: int = 0


class EvaluationResponse(BaseModel):
    id: int
    attempt_id: int
    verdict: str
    rubric_score: float
    feedback: str
    confidence: str
    concept_progress_status: str | None = None
    concept_progress_estimate: float | None = None

    model_config = {"from_attributes": True}
