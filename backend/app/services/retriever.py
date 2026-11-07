import numpy as np
from sqlalchemy.orm import Session

from app.models.chunk import Chunk, EMBEDDING_DIM
from app.services.embedder import embed_query

TOP_K = 5


def retrieve_chunks(db: Session, course_id: int, question: str) -> list[Chunk]:
    """
    Embed the question and return the top-K chunks from the given course,
    ordered by cosine similarity.
    """
    query_vector = embed_query(question)
    q_vec = np.array(query_vector, dtype=float)
    q_norm = np.linalg.norm(q_vec)
    if q_norm > 0:
        q_vec = q_vec / q_norm

    # Fetch candidate chunks for this course
    chunks = (
        db.query(Chunk)
        .join(Chunk.document)
        .filter(Chunk.document.has(course_id=course_id))
        .filter(Chunk.embedding.isnot(None))
        .all()
    )

    if not chunks:
        return []

    # Calculate cosine similarity for each chunk
    scored_chunks = []
    for chunk in chunks:
        c_vec = np.array(chunk.embedding, dtype=float)
        c_norm = np.linalg.norm(c_vec)
        if c_norm > 0:
            c_vec = c_vec / c_norm
        similarity = float(np.dot(q_vec, c_vec))
        scored_chunks.append((similarity, chunk))

    # Sort descending by similarity score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored_chunks[:TOP_K]]
