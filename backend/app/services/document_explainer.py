import json
from groq import Groq
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.concept import Concept
from app.models.document import Document

MODEL = "openai/gpt-oss-120b"


def explain_and_summarize_document(db: Session, document: Document) -> dict:
    """
    Reads the document's chunks and generates a comprehensive student-friendly
    resume, detailed conceptual explanation, and extracts key concepts.
    """
    chunks = sorted(document.chunks, key=lambda c: (c.page_start, c.id))
    full_text = "\n\n".join(c.text for c in chunks if c.text)

    if not full_text.strip():
        return {
            "title": document.filename,
            "resume": "No readable text could be extracted from this document.",
            "explanation": "This document contains no readable pages or text.",
            "key_concepts": [],
            "takeaways": [],
        }

    # Truncate to reasonable context window
    truncated_text = full_text[:25_000]

    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = f"""You are StudyMate, a world-class academic tutor and professor.
Read the following student study material extracted from '{document.filename}'.
Analyze it thoroughly and produce a structured JSON response with:
1. "resume": A comprehensive 2-3 paragraph academic resume / executive summary of the entire document. Explain what it covers, its central thesis or objective, and its importance.
2. "explanation": A detailed, easy-to-understand explanation of the material for a student. Break down complex theories, explain formulas or terminology in plain English, and provide intuitive analogies.
3. "takeaways": A list of 4 to 6 key takeaways or principles that every student must remember.
4. "key_concepts": A list of 3 to 6 core concepts found in this document. Each item must have:
   - "name": Concise name of the concept
   - "description": 1-2 sentence definition or explanation

STUDY MATERIAL:
\"\"\"
{truncated_text}
\"\"\"

Respond with ONLY a single valid JSON object with keys: "resume", "explanation", "takeaways", "key_concepts". Do not include markdown code block formatting.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a master academic educator and tutor. Output raw JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=2048,
        )
        content = response.choices[0].message.content or "{}"
        if content.startswith("```json"):
            content = content.replace("```json", "", 1).rstrip("`").strip()
        elif content.startswith("```"):
            content = content.replace("```", "", 1).rstrip("`").strip()

        data = json.loads(content)
    except Exception as exc:
        data = {
            "resume": f"Material from {document.filename}. Explores foundational concepts in {document.filename}.",
            "explanation": f"This document provides essential study material regarding {document.filename}. Review the core chapters to master the foundational mechanics.",
            "takeaways": ["Review primary definitions", "Understand the foundational workflows", "Apply concepts to practice problems"],
            "key_concepts": [{"name": "Core Principles", "description": "Foundational ideas introduced in the lecture notes."}],
        }

    # Save summary and explanation to document record
    document.summary = data.get("resume", "")
    document.explanation = data.get("explanation", "")
    db.add(document)

    # Seed concepts into Course Concepts so student progress tracks them
    key_concepts = data.get("key_concepts", [])
    for kc in key_concepts:
        c_name = kc.get("name", "").strip()
        c_desc = kc.get("description", "").strip()
        if c_name:
            existing = (
                db.query(Concept)
                .filter(Concept.course_id == document.course_id, Concept.name.ilike(c_name))
                .first()
            )
            if not existing:
                db.add(Concept(
                    course_id=document.course_id,
                    name=c_name,
                    description=c_desc,
                    domain_type="foundational",
                ))

    db.commit()
    db.refresh(document)
    return data
