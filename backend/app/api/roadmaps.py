from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.roadmap_node import RoadmapNode
from app.models.roadmap_node_progress import RoadmapNodeProgress
from app.models.user_roadmap import UserRoadmap
from app.services.roadmap_service import generate_roadmap_from_llm, persist_roadmap

router = APIRouter(tags=["roadmaps"])

VALID_NODE_STATUSES = {"not-started", "in-progress", "completed", "known"}


def _current_user_id(x_user_id: int = Header(...)) -> int:
    return x_user_id


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class GenerateRoadmapRequest(BaseModel):
    role: str


class CreateRoadmapBody(BaseModel):
    role: str
    category: str | None = "Engineering"
    goal: str | None = None


class RoadmapNodeResponse(BaseModel):
    id: int
    title: str
    description: str | None
    order: int
    optional: bool
    prerequisite_id: int | None

    model_config = {"from_attributes": True}


class RoadmapResponse(BaseModel):
    id: int
    role: str
    description: str | None
    source: str
    nodes: list[RoadmapNodeResponse]

    model_config = {"from_attributes": True}


class EnrollRoadmapRequest(BaseModel):
    roadmap_id: int


class NodeProgressResponse(BaseModel):
    id: int
    node_id: int
    status: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserRoadmapResponse(BaseModel):
    id: int
    roadmap_id: int
    status: str
    enrolled_at: datetime
    node_progress: list[NodeProgressResponse] = []

    model_config = {"from_attributes": True}


class PatchNodeStatusRequest(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/roadmaps", response_model=list[RoadmapResponse])
def list_roadmaps(db: Session = Depends(get_db)):
    from app.models.roadmap import Roadmap
    return db.query(Roadmap).all()


@router.get("/roadmaps/{roadmap_id}", response_model=RoadmapResponse)
def get_roadmap(roadmap_id: str, db: Session = Depends(get_db)):
    from app.models.roadmap import Roadmap
    from app.models.roadmap_node import RoadmapNode

    r = None
    if roadmap_id.isdigit():
        r = db.get(Roadmap, int(roadmap_id))

    if not r:
        role_search = roadmap_id.replace("-", " ").strip()
        r = db.query(Roadmap).filter(Roadmap.role.ilike(f"%{role_search}%")).first()

    if not r:
        parts = roadmap_id.replace("-", " ").strip().split()
        for p in parts:
            if len(p) > 3:
                r = db.query(Roadmap).filter(Roadmap.role.ilike(f"%{p}%")).first()
                if r:
                    break

    if not r:
        # Fallback to first roadmap or auto-seed
        r = db.query(Roadmap).first()

    if not r:
        role_title = roadmap_id.replace("-", " ").title()
        r = Roadmap(
            role=role_title,
            description=f"Complete step-by-step learning roadmap for {role_title}.",
            source="Curated by Study Partner",
        )
        db.add(r)
        db.flush()

        default_nodes = [
            ("Core Foundations", f"Essential fundamentals of {role_title}.", False),
            ("Key Tools & Frameworks", "Standard workflows and production toolsets.", False),
            ("Intermediate Architecture", "Scalable design patterns and state management.", False),
            ("Testing & Performance", "Automated testing, debugging and performance optimization.", False),
            ("Advanced Specialization", "Cutting-edge techniques and advanced topics.", True),
        ]
        for order, (t_title, t_desc, opt) in enumerate(default_nodes, start=1):
            db.add(RoadmapNode(
                roadmap_id=r.id,
                title=t_title,
                description=t_desc,
                order=order,
                optional=opt,
            ))
        db.commit()
        db.refresh(r)

    return r


@router.post("/roadmaps", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
def create_roadmap(
    body: CreateRoadmapBody,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    from app.models.roadmap import Roadmap
    from app.models.roadmap_node import RoadmapNode

    desc = body.goal or f"Learning path to become a {body.role}."
    roadmap = Roadmap(
        role=body.role,
        description=desc,
        source="AI-generated mock",
    )
    db.add(roadmap)
    db.flush()

    default_topics = [
        ("Foundations & Principles", "Core introductory concepts and mental models.", False),
        ("Tools & Workflows", "Industry standard toolset and practical workflows.", False),
        ("Applied Projects", "Hands-on implementation of real-world scenarios.", False),
        ("Advanced Techniques", "Specialized patterns and optimization strategies.", True),
    ]
    for order, (t_title, t_desc, opt) in enumerate(default_topics, start=1):
        db.add(RoadmapNode(
            roadmap_id=roadmap.id,
            title=t_title,
            description=t_desc,
            order=order,
            optional=opt,
        ))

    db.commit()
    db.refresh(roadmap)
    return roadmap


@router.post("/roadmaps/generate", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
def generate_roadmap(
    body: GenerateRoadmapRequest,
    db: Session = Depends(get_db),
    _: int = Depends(_current_user_id),
):
    schema = generate_roadmap_from_llm(body.role.strip())
    roadmap = persist_roadmap(db, schema)
    db.commit()
    db.refresh(roadmap)
    return roadmap


@router.post("/user-roadmaps", response_model=UserRoadmapResponse, status_code=status.HTTP_201_CREATED)
def enroll_roadmap(
    body: EnrollRoadmapRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    from app.models.roadmap import Roadmap

    roadmap = db.get(Roadmap, body.roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    user_roadmap = UserRoadmap(user_id=user_id, roadmap_id=roadmap.id)
    db.add(user_roadmap)
    db.flush()

    # Seed a RoadmapNodeProgress row for every node
    for node in roadmap.nodes:
        db.add(RoadmapNodeProgress(user_roadmap_id=user_roadmap.id, node_id=node.id, status="not-started"))

    db.commit()
    db.refresh(user_roadmap)
    return user_roadmap


@router.patch("/user-roadmaps/{user_roadmap_id}/nodes/{node_id}", response_model=NodeProgressResponse)
def update_node_status(
    user_roadmap_id: int,
    node_id: int,
    body: PatchNodeStatusRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    if body.status not in VALID_NODE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"status must be one of {sorted(VALID_NODE_STATUSES)}",
        )

    user_roadmap = (
        db.query(UserRoadmap)
        .filter(UserRoadmap.id == user_roadmap_id, UserRoadmap.user_id == user_id)
        .first()
    )
    if not user_roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UserRoadmap not found")

    node = db.query(RoadmapNode).filter(
        RoadmapNode.id == node_id,
        RoadmapNode.roadmap_id == user_roadmap.roadmap_id,
    ).first()
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found in this roadmap")

    node_prog = (
        db.query(RoadmapNodeProgress)
        .filter(
            RoadmapNodeProgress.user_roadmap_id == user_roadmap_id,
            RoadmapNodeProgress.node_id == node_id,
        )
        .first()
    )
    if node_prog:
        node_prog.status = body.status
        node_prog.updated_at = datetime.now(timezone.utc)
    else:
        node_prog = RoadmapNodeProgress(
            user_roadmap_id=user_roadmap_id,
            node_id=node_id,
            status=body.status,
        )
        db.add(node_prog)

    db.commit()
    db.refresh(node_prog)
    return node_prog
