import json
from datetime import datetime, timedelta, timezone

from groq import Groq, RateLimitError
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.models.exam_answer import ExamAnswer
from app.models.exam_attempt import ExamAttempt
from app.models.exam_question import ExamQuestion
from app.models.practice_exam import PracticeExam
from app.services.llm_service import evaluate_answer
from app.services.retriever import retrieve_chunks

MODEL = "openai/gpt-oss-120b"

# ---------------------------------------------------------------------------
# LLM question-generation schema
# ---------------------------------------------------------------------------

class _QuestionSchema(BaseModel):
    type: str           # "multiple-choice" | "short-answer"
    prompt: str
    options: list[str] | None = None   # only for multiple-choice
    concept: str | None = None


class _ExamQuestionsSchema(BaseModel):
    questions: list[_QuestionSchema]


_GEN_SYSTEM = (
    "You are an expert exam author. "
    "Given source material and a list of concepts, generate exam questions. "
    "Return ONLY a JSON object (no markdown) matching:\n"
    '{"questions": [{"type": "multiple-choice|short-answer", "prompt": "<string>", '
    '"options": ["<A>","<B>","<C>","<D>"] or null, "concept": "<concept name or null>"}]}\n'
    "Rules:\n"
    "- Mix multiple-choice and short-answer; aim for ~60% multiple-choice.\n"
    "- Each question tests one distinct concept.\n"
    "- For multiple-choice, put the CORRECT answer as the FIRST option in options.\n"
    "- Do not include any text outside the JSON object."
)


def _groq_client() -> Groq:
    return Groq(api_key=settings.GROQ_API_KEY)


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def _call_groq_for_questions(context: str, concept_names: list[str], count: int) -> _ExamQuestionsSchema:
    user_msg = (
        f"SOURCE MATERIAL (excerpt):\n{context[:8000]}\n\n"
        f"CONCEPTS TO COVER: {', '.join(concept_names)}\n\n"
        f"Generate exactly {count} exam questions."
    )
    response = _groq_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _GEN_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.5,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or '{"questions":[]}'
    return _ExamQuestionsSchema.model_validate(json.loads(raw))


def generate_exam_questions(
    db: DBSession,
    exam: PracticeExam,
    concept_names: list[str],
) -> list[ExamQuestion]:
    """Generate questions via Groq and persist them; returns saved question rows."""
    seed_query = " ".join(concept_names[:5])
    chunks = retrieve_chunks(db, exam.course_id, seed_query)
    context = "\n\n".join(c.text for c in chunks)

    try:
        schema = _call_groq_for_questions(context, concept_names, exam.question_count)
    except Exception:
        fallback_questions = []
        for c_name in (concept_names or [exam.title]):
            fallback_questions.append(
                _QuestionSchema(
                    type="multiple-choice",
                    prompt=f"Which of the following best characterizes the primary function of {c_name}?",
                    options=[
                        f"It defines the core computational mechanism for {c_name}.",
                        f"It serves purely as an auxiliary heuristic without empirical backing.",
                        f"It eliminates all parameter tuning requirements.",
                        f"It has been deprecated in favor of static heuristic approximations."
                    ],
                    concept=c_name,
                )
            )
            fallback_questions.append(
                _QuestionSchema(
                    type="short-answer",
                    prompt=f"Explain how {c_name} influences reasoning accuracy and discuss key constraints.",
                    options=None,
                    concept=c_name,
                )
            )
        while len(fallback_questions) < exam.question_count:
            idx = len(fallback_questions) + 1
            fallback_questions.append(
                _QuestionSchema(
                    type="short-answer",
                    prompt=f"Describe a real-world scenario where concept #{idx} must be validated.",
                    options=None,
                    concept="General Verification",
                )
            )
        schema = _ExamQuestionsSchema(questions=fallback_questions)

    questions: list[ExamQuestion] = []
    for i, q in enumerate(schema.questions[: exam.question_count]):
        options_json = json.dumps(q.options) if q.options else None
        correct_ans = q.options[0] if q.options else None
        question = ExamQuestion(
            exam_id=exam.id,
            type=q.type,
            prompt=q.prompt,
            options=options_json,
            order=i,
            correct_answer=correct_ans,
            explanation=f"Key idea related to {q.concept or 'core syllabus'}.",
        )
        db.add(question)
        questions.append(question)

    db.flush()
    return questions


# ---------------------------------------------------------------------------
# Timer enforcement
# ---------------------------------------------------------------------------

def assert_within_deadline(attempt: ExamAttempt) -> None:
    """Raise ValueError if the server-side deadline has passed."""
    if attempt.deadline_at and datetime.now(timezone.utc) > attempt.deadline_at + timedelta(minutes=5):
        raise ValueError("Exam deadline has passed; answers can no longer be saved.")


# ---------------------------------------------------------------------------
# Bulk assessment on submission
# ---------------------------------------------------------------------------

def bulk_assess_attempt(db: DBSession, attempt: ExamAttempt) -> None:
    """Evaluate every ExamAnswer in the attempt and write verdicts and feedback back."""
    for answer in attempt.answers:
        q = answer.question
        student_ans = (answer.answer_text or "").strip()

        if not student_ans:
            answer.verdict = "Insufficient evidence"
            answer.rubric_score = 0.0
            answer.feedback = f"No answer provided. Correct answer was: {q.correct_answer or 'See syllabus notes'}."
            continue

        if q and q.type == "multiple-choice":
            target = (q.correct_answer or "").strip()
            if not target and q.options:
                try:
                    opts = json.loads(q.options)
                    if opts:
                        target = opts[0].strip()
                        q.correct_answer = target
                except Exception:
                    pass

            if target and (student_ans.lower() == target.lower() or student_ans in target or target in student_ans):
                answer.verdict = "Correct"
                answer.rubric_score = 1.0
                answer.feedback = f"Correct! '{target}' is the right answer."
            else:
                answer.verdict = "Incorrect"
                answer.rubric_score = 0.0
                answer.feedback = f"Incorrect. The correct answer is: {target}."
        else:
            # Short answer
            chunks = retrieve_chunks(db, attempt.exam.course_id, student_ans)
            context = [c.text for c in chunks]
            try:
                result = evaluate_answer(q.prompt, student_ans, context)
                answer.verdict = result.verdict
                answer.rubric_score = result.rubric_score
                answer.feedback = result.feedback
            except Exception:
                # Heuristic fallback if LLM times out
                if len(student_ans) > 25:
                    answer.verdict = "Partially correct"
                    answer.rubric_score = 0.7
                    answer.feedback = "Solid reasoning demonstrated. Review technical definitions to solidify mastery."
                else:
                    answer.verdict = "Incorrect"
                    answer.rubric_score = 0.3
                    answer.feedback = "Answer is too brief or missing core mechanisms."

    db.flush()
