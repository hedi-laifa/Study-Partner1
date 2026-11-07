from datetime import datetime
from pydantic import BaseModel


class SessionCreate(BaseModel):
    course_id: int
    goal: str | None = None
    knowledge_mode: str = "course-grounded"


class ActivityResponse(BaseModel):
    id: int
    session_id: int
    concept_id: int | None
    type: str
    difficulty: str
    prompt: str
    mode: str

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: int
    course_id: int
    goal: str | None
    status: str
    knowledge_mode: str
    created_at: datetime
    activities: list[ActivityResponse] = []

    model_config = {"from_attributes": True}


class NextActivityRequest(BaseModel):
    answer: str
    hint_count: int = 0
