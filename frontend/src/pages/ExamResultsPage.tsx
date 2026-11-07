import { AlertCircle, ArrowLeft, ArrowRight, CheckCircle2, ChevronDown, ChevronUp, Clock3, Compass, Target, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { EmptyState } from '../components/feedback/EmptyState'
import { ProgressBar } from '../components/ui/ProgressBar'
import { examService } from '../services/api-client'
import type { ExamQuestionResult, ExamResult, ExamVerdict } from '../services/contracts/exams'

const verdicts: ExamVerdict[] = ['Correct', 'Partially correct', 'Incorrect', 'Insufficient evidence']

export function ExamResultsPage() {
  const { examId } = useParams()
  const [result, setResult] = useState<ExamResult>()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!examId) return
    void examService.getResult(examId).then((value) => {
      setResult(value)
      setLoading(false)
    })
  }, [examId])

  if (loading) return <div className="exam-results-loading" role="status">Preparing your practice feedback…</div>
  if (!result) return <EmptyState title="Practice result not found" text="This result may have expired. Return to the exams library and try another practice exam." />

  return (
    <div className="page-stack exam-results-page">
      <Link to="/exams" className="back-link"><ArrowLeft size={15} /> Exams library</Link>
      <section className="exam-results-hero">
        <div>
          <span className="eyebrow">Practice feedback · {result.course}</span>
          <h2>{result.title}</h2>
          <p>Review your answers and verified correct solutions below.</p>
        </div>
        <div className="practice-signal">
          <strong>{result.scoreLabel}</strong>
          <span>Final Score</span>
        </div>
      </section>

      <div className="exam-results-actions">
        <Link to={`/courses/${result.courseId}`} className="text-link">Back to course <ArrowRight size={14} /></Link>
        <Link to="/progress" className="text-link">View study progress <Compass size={14} /></Link>
      </div>

      <div className="exam-results-summary-grid">
        <SummaryStat icon={<CheckCircle2 size={17} />} label="Completed" value={`${result.completedQuestions}/${result.totalQuestions}`} detail="questions answered" />
        <SummaryStat icon={<Clock3 size={17} />} label="Status" value="Graded" detail="verified solutions" />
        <SummaryStat icon={<Target size={17} />} label="Correct" value={`${result.counts.Correct}`} detail="correct responses" />
      </div>

      <section className="verdict-counts">
        {verdicts.map((verdict) => (
          <div className={`verdict-count ${verdictClass(verdict)}`} key={verdict}>
            <VerdictIcon verdict={verdict} />
            <strong>{result.counts[verdict]}</strong>
            <span>{verdict}</span>
          </div>
        ))}
      </section>

      <div className="exam-results-grid">
        <section className="progress-panel question-results-panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Review your reasoning & answers</span>
              <h2>Question feedback & Solutions</h2>
            </div>
          </div>
          <div className="question-result-list">
            {result.questionResults.map((item, index) => (
              <QuestionResult item={item} index={index} key={item.question.id || index} />
            ))}
          </div>
        </section>

        <aside className="progress-panel concept-performance-panel">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Patterns across the exam</span>
              <h2>Concept performance</h2>
            </div>
          </div>
          <div className="concept-result-list">
            {result.concepts.map((concept) => (
              <div className="concept-result" key={concept.concept}>
                <div className="concept-result-heading">
                  <strong>{concept.concept}</strong>
                  <span>{concept.correct}/{concept.total} correct</span>
                </div>
                <ProgressBar
                  value={concept.total ? (concept.correct / concept.total) * 100 : 0}
                  color={concept.correct === concept.total ? 'green' : 'orange'}
                />
                <p>{concept.summary}</p>
                <small><strong>Next:</strong> {concept.nextAction}</small>
                <Link className="text-link" to={`/courses`}>
                  Review course materials <ArrowRight size={13} />
                </Link>
              </div>
            ))}
          </div>
        </aside>
      </div>
      <p className="exam-results-disclaimer">
        <AlertCircle size={15} /> Evaluated with StudyMate Automated Grading. Review the correct solutions to reinforce your knowledge.
      </p>
    </div>
  )
}

function SummaryStat({ icon, label, value, detail }: { icon: ReactNode; label: string; value: string; detail: string }) {
  return (
    <div className="stat-card">
      <div className="stat-icon green">{icon}</div>
      <div>
        <span className="muted">{label}</span>
        <strong className="stat-value">{value}</strong>
        <span className="stat-detail">{detail}</span>
      </div>
    </div>
  )
}

function QuestionResult({ item, index }: { item: ExamQuestionResult; index: number }) {
  const [open, setOpen] = useState(true)

  const isCorrect = item.verdict === 'Correct'

  return (
    <article className={`question-result ${open ? 'open' : ''}`}>
      <button className="question-result-toggle" onClick={() => setOpen((value) => !value)} aria-expanded={open}>
        <span className="question-result-number">{index + 1}</span>
        <span className="question-result-title">
          <strong>{item.question.prompt}</strong>
          <small>{item.question.concept}</small>
        </span>
        <span className={`status-label ${verdictClass(item.verdict)}`}>{item.verdict}</span>
        {open ? <ChevronUp size={17} /> : <ChevronDown size={17} />}
      </button>

      {open && (
        <div className="question-result-body">
          {/* Student Answer */}
          <div className="answer-review">
            <span className="eyebrow">Your submitted answer</span>
            <p style={{ fontWeight: 500, color: isCorrect ? '#166534' : '#991b1b', margin: '4px 0 0' }}>
              {item.answer || '(No answer provided)'}
            </p>
          </div>

          {/* Correct Answer Box */}
          <div
            style={{
              background: '#f0fdf4',
              border: '1px solid #86efac',
              borderRadius: '8px',
              padding: '14px 18px',
              margin: '12px 0',
            }}
          >
            <span
              style={{
                color: '#15803d',
                fontSize: '0.82rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                marginBottom: '4px',
              }}
            >
              <CheckCircle2 size={16} /> Verified Correct Answer
            </span>
            <p style={{ margin: 0, fontWeight: 600, color: '#166534', fontSize: '1rem', lineHeight: 1.5 }}>
              {item.correctAnswer || item.expectedIdeas?.[0] || 'Refer to core concept definitions'}
            </p>
          </div>

          <div className="feedback-columns">
            <FeedbackList
              title="Feedback & Strengths"
              items={item.strengths.length ? item.strengths : isCorrect ? ['Accurate terminology and understanding.'] : []}
              empty={isCorrect ? 'Accurate terminology and understanding.' : undefined}
            />
            <FeedbackList
              title="Gaps & Areas to Review"
              items={item.gaps}
              empty={isCorrect ? 'No gaps identified. Complete mastery demonstrated.' : 'Review relevant lecture notes.'}
            />
          </div>

          <div className="question-confidence">
            <span>Grading Confidence</span>
            <strong>{item.confidence}</strong>
          </div>
        </div>
      )}
    </article>
  )
}

function FeedbackList({ title, items, empty }: { title: string; items: string[]; empty?: string }) {
  return (
    <div>
      <strong>{title}</strong>
      {items.length ? (
        <ul>
          {items.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="feedback-empty">{empty || 'None'}</p>
      )}
    </div>
  )
}

function VerdictIcon({ verdict }: { verdict: ExamVerdict }) {
  if (verdict === 'Correct') return <CheckCircle2 size={16} />
  if (verdict === 'Incorrect') return <XCircle size={16} />
  return <AlertCircle size={16} />
}

function verdictClass(verdict: ExamVerdict) {
  return verdict.toLowerCase().replaceAll(' ', '-')
}
