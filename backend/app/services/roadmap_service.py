import json
from datetime import datetime, timezone
from functools import lru_cache

from groq import Groq, RateLimitError
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.models.concept_progress import ConceptProgress
from app.models.roadmap import Roadmap
from app.models.roadmap_node import RoadmapNode
from app.models.roadmap_node_progress import RoadmapNodeProgress
from app.models.user_roadmap import UserRoadmap

MODEL = "openai/gpt-oss-120b"

# ---------------------------------------------------------------------------
# LLM schema
# ---------------------------------------------------------------------------

class RoadmapNodeSchema(BaseModel):
    title: str
    description: str
    order: int
    optional: bool = False
    prerequisite_title: str | None = None   # title of the prerequisite node, or null


class RoadmapSchema(BaseModel):
    role: str
    description: str
    nodes: list[RoadmapNodeSchema]


_SYSTEM_PROMPT = (
    "You are a curriculum design expert. "
    "Given a professional role, generate a structured learning roadmap. "
    "Return ONLY a JSON object matching this schema (no markdown, no commentary):\n"
    "{\n"
    '  "role": "<string>",\n'
    '  "description": "<one sentence>",\n'
    '  "nodes": [\n'
    "    {\n"
    '      "title": "<string>",\n'
    '      "description": "<string>",\n'
    '      "order": <int starting at 1>,\n'
    '      "optional": <bool>,\n'
    '      "prerequisite_title": "<title of prerequisite node or null>"\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "Rules:\n"
    "- Produce 8–14 nodes ordered from foundational to advanced.\n"
    "- prerequisite_title must match another node's title exactly, or be null.\n"
    "- Mark supplementary nodes as optional: true.\n"
    "- Do not include any text outside the JSON object."
)


@lru_cache(maxsize=1)
def _client() -> Groq:
    return Groq(api_key=settings.GROQ_API_KEY)


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def generate_roadmap_from_llm(role: str) -> RoadmapSchema:
    response = _client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Generate a learning roadmap for: {role}"},
        ],
        temperature=0.4,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    return RoadmapSchema.model_validate(json.loads(raw))


# ---------------------------------------------------------------------------
# DB persistence
# ---------------------------------------------------------------------------

def persist_roadmap(db: DBSession, schema: RoadmapSchema) -> Roadmap:
    roadmap = Roadmap(role=schema.role, description=schema.description, source="generated")
    db.add(roadmap)
    db.flush()

    # First pass: create all nodes without prerequisites
    title_to_node: dict[str, RoadmapNode] = {}
    for n in schema.nodes:
        node = RoadmapNode(
            roadmap_id=roadmap.id,
            title=n.title,
            description=n.description,
            order=n.order,
            optional=n.optional,
        )
        db.add(node)
        db.flush()
        title_to_node[n.title] = node

    # Second pass: wire prerequisites
    for n in schema.nodes:
        if n.prerequisite_title and n.prerequisite_title in title_to_node:
            title_to_node[n.title].prerequisite_id = title_to_node[n.prerequisite_title].id

    db.flush()
    return roadmap


# ---------------------------------------------------------------------------
# Sync ConceptProgress → RoadmapNodeProgress
# ---------------------------------------------------------------------------

# Map concept-progress status values to node-progress status values
_STATUS_MAP = {
    "good-evidence": "completed",
    "developing": "in-progress",
    "needs-practice": "in-progress",
    "not-enough-evidence": "not-started",
}


def sync_node_progress_from_concept(
    db: DBSession,
    user_roadmap_id: int,
    concept_id: int,
) -> None:
    """
    When a ConceptProgress row changes, update the matching RoadmapNodeProgress
    rows whose node title matches the concept name (case-insensitive).
    """
    from app.models.concept import Concept  # local import avoids circular deps

    progress = db.query(ConceptProgress).filter(ConceptProgress.concept_id == concept_id).first()
    if not progress:
        return

    concept = db.get(Concept, concept_id)
    if not concept:
        return

    mapped_status = _STATUS_MAP.get(progress.status, "not-started")

    # Find roadmap nodes whose title matches the concept name in this user roadmap
    user_roadmap = db.get(UserRoadmap, user_roadmap_id)
    if not user_roadmap:
        return

    matching_nodes = (
        db.query(RoadmapNode)
        .filter(
            RoadmapNode.roadmap_id == user_roadmap.roadmap_id,
            RoadmapNode.title.ilike(concept.name),
        )
        .all()
    )

    for node in matching_nodes:
        node_prog = (
            db.query(RoadmapNodeProgress)
            .filter(
                RoadmapNodeProgress.user_roadmap_id == user_roadmap_id,
                RoadmapNodeProgress.node_id == node.id,
            )
            .first()
        )
        if node_prog:
            node_prog.status = mapped_status
            node_prog.updated_at = datetime.now(timezone.utc)
        else:
            db.add(RoadmapNodeProgress(
                user_roadmap_id=user_roadmap_id,
                node_id=node.id,
                status=mapped_status,
            ))
    db.flush()
