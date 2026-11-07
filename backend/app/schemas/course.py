from pydantic import BaseModel


class CourseCreate(BaseModel):
    title: str
    subject: str | None = None
    domain_type: str | None = None


class CourseResponse(BaseModel):
    id: int
    user_id: int
    title: str
    subject: str | None
    domain_type: str | None

    model_config = {"from_attributes": True}
