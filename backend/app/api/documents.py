import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.chunk import Chunk
from app.models.course import Course
from app.models.document import Document
from app.services.chunker import chunk_pages
from app.services.document_explainer import explain_and_summarize_document
from app.services.embedder import embed_texts
from app.services.llm_service import generate_tutor_response
from app.services.pdf_extractor import extract_pages

router = APIRouter(prefix="/courses", tags=["documents"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}


def _current_user_id(x_user_id: int | None = Header(None)) -> int:
    return x_user_id or 1


def _find_course(db: Session, course_id: str, user_id: int) -> Course | None:
    if course_id.isdigit():
        c = db.query(Course).filter(Course.id == int(course_id), Course.user_id == user_id).first()
        if c:
            return c
    title_search = course_id.replace("-", " ").strip()
    c = db.query(Course).filter(Course.user_id == user_id, Course.title.ilike(f"%{title_search}%")).first()
    if c:
        return c
    if course_id.isdigit():
        return db.get(Course, int(course_id))
    return None


class DocumentChatRequest(BaseModel):
    question: str


@router.post("/{course_id}/documents", status_code=status.HTTP_201_CREATED)
def upload_document(
    course_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only PDF files are accepted")

    course = _find_course(db, course_id, user_id)
    if not course:
        # Create a course for this user if not found
        course = Course(
            user_id=user_id,
            title=course_id.replace("-", " ").title(),
            subject="General Studies",
            domain_type="Intermediate",
        )
        db.add(course)
        db.commit()
        db.refresh(course)

    real_course_id = course.id

    # Persist document record isolated to this course and user
    doc = Document(course_id=real_course_id, filename=file.filename or "upload.pdf", status="processing")
    db.add(doc)
    db.flush()

    # Save file to user-specific upload directory
    upload_dir: Path = settings.UPLOAD_DIR / f"user_{user_id}" / str(real_course_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / f"{doc.id}_{file.filename}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        page_records = extract_pages(dest)
        pages_for_chunker = [
            (p.page_number, p.text)
            for p in page_records
            if not p.low_text
        ]

        if not pages_for_chunker:
            doc.status = "no_text"
            db.commit()
            return {"id": doc.id, "status": doc.status, "chunks": 0}

        chunks = chunk_pages(pages_for_chunker)
        texts = [c.text for c in chunks]
        vectors = embed_texts(texts)

        for chunk, vector in zip(chunks, vectors):
            db.add(Chunk(
                document_id=doc.id,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                text=chunk.text,
                embedding=vector,
            ))

        doc.status = "ready"
        db.commit()
        db.refresh(doc)

        # Automatically generate explanation and resume in background/inline
        try:
            explain_and_summarize_document(db, doc)
        except Exception:
            pass

    except Exception as exc:
        db.rollback()
        doc.status = "error"
        db.add(doc)
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return {"id": doc.id, "status": doc.status, "chunks": len(chunks)}


@router.get("/{course_id}/documents")
def list_documents(
    course_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    course = _find_course(db, course_id, user_id)
    if not course:
        return []

    docs = db.query(Document).filter(Document.course_id == course.id).all()
    return [
        {
            "id": str(d.id),
            "courseId": str(course.id),
            "fileName": d.filename,
            "filename": d.filename,
            "sizeBytes": 1024 * 1024,
            "status": "Ready" if d.status == "ready" else "Processing" if d.status == "processing" else "Failed",
            "addedAt": "Recently",
            "chunks": len(d.chunks),
            "hasExplanation": bool(d.summary or d.explanation),
        }
        for d in docs
    ]


@router.get("/{course_id}/documents/{document_id}/explanation")
def get_document_explanation(
    course_id: str,
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    result = explain_and_summarize_document(db, doc)
    return {
        "id": doc.id,
        "filename": doc.filename,
        "resume": result.get("resume") or doc.summary,
        "explanation": result.get("explanation") or doc.explanation,
        "takeaways": result.get("takeaways", []),
        "key_concepts": result.get("key_concepts", []),
        "chunkCount": len(doc.chunks),
    }


@router.post("/{course_id}/documents/{document_id}/chat")
def chat_document(
    course_id: str,
    document_id: int,
    body: DocumentChatRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    chunks = [c.text for c in doc.chunks if c.text][:8]
    if not chunks:
        return {"answer": "No readable material found in this document to answer from."}

    answer = generate_tutor_response(body.question, chunks)
    return {"answer": answer}


@router.delete("/{course_id}/documents/{document_id}")
def delete_document(
    course_id: str,
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(_current_user_id),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return {"status": "ok"}
    db.delete(doc)
    db.commit()
    return {"status": "ok"}
