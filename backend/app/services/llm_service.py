import json
from functools import lru_cache

from groq import Groq, RateLimitError
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

MODEL = "openai/gpt-oss-120b"
MAX_CONTEXT_CHARS = 12_000  # stay well within the 128k context window


@lru_cache(maxsize=1)
def _client() -> Groq:
    return Groq(api_key=settings.GROQ_API_KEY)


def _build_system_prompt(context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks[:5])[:MAX_CONTEXT_CHARS]
    return (
        "You are StudyMate, a knowledgeable and encouraging academic tutor. "
        "Answer the student's question using ONLY the provided source material. "
        "If the material does not contain enough information, say so clearly rather than guessing.\n\n"
        f"SOURCE MATERIAL:\n{context}"
    )


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def generate_tutor_response(prompt: str, context_chunks: list[str]) -> str:
    response = _client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _build_system_prompt(context_chunks)},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Structured evaluation
# ---------------------------------------------------------------------------

class EvaluationResult(BaseModel):
    verdict: str          # "Correct" | "Partially correct" | "Incorrect" | "Insufficient evidence"
    rubric_score: float   # 0.0 – 1.0
    confidence: str       # "High" | "Medium" | "Low"
    strengths: list[str]
    gaps: list[str]
    feedback: str


_EVAL_SYSTEM = (
    "You are an expert academic assessor. "
    "Evaluate the student's answer against the question and source material. "
    "Respond with a single JSON object matching this schema exactly (no markdown):\n"
    '{"verdict": "Correct|Partially correct|Incorrect|Insufficient evidence", '
    '"rubric_score": <float 0.0-1.0>, '
    '"confidence": "High|Medium|Low", '
    '"strengths": [<string>, ...], '
    '"gaps": [<string>, ...], '
    '"feedback": "<one-paragraph summary>"}'
)


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def evaluate_answer(
    question: str,
    answer: str,
    context_chunks: list[str],
) -> EvaluationResult:
    context = "\n\n---\n\n".join(context_chunks[:5])[:MAX_CONTEXT_CHARS]
    user_msg = (
        f"SOURCE MATERIAL:\n{context}\n\n"
        f"QUESTION:\n{question}\n\n"
        f"STUDENT ANSWER:\n{answer}"
    )
    response = _client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _EVAL_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.1,
        max_tokens=512,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    return EvaluationResult.model_validate(json.loads(raw))
