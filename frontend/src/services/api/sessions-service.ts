import apiClient from '../apiClient'
import type {
  StudyFeedback,
  StudyQuestion,
  StudySessionDetail,
  StudySessionService,
} from '../contracts/sessions'

interface BackendActivity {
  id: number
  session_id: number
  concept_id: number | null
  type: string
  difficulty: string
  prompt: string
  mode: string
}

interface BackendSession {
  id: number
  course_id: number
  goal: string | null
  status: string
  knowledge_mode: string
  created_at: string
  activities: BackendActivity[]
}

interface BackendEvaluation {
  id: number
  attempt_id: number
  verdict: string
  rubric_score: number
  feedback: string
  confidence: string
}

// Stores the backend session id keyed by the frontend session id
const sessionIdMap = new Map<string, number>()

function mapActivityToQuestion(activity: BackendActivity, goal: string): StudyQuestion {
  return {
    id: String(activity.id),
    topic: goal || 'Study session',
    prompt: activity.prompt,
    context: undefined,
    hints: [],
    explanation: '',
    sources: [],
    scenarios: [],
  }
}

function mapEvaluationToFeedback(evaluation: BackendEvaluation): StudyFeedback {
  const isCorrect = evaluation.verdict === 'correct' || evaluation.verdict === 'pass' || evaluation.rubric_score >= 0.7
  const isPartial = !isCorrect && evaluation.rubric_score >= 0.4

  const verdict = isCorrect
    ? 'Correct'
    : isPartial
    ? 'Partially correct'
    : 'Needs review'

  return {
    verdict: verdict as StudyFeedback['verdict'],
    strengths: isCorrect || isPartial ? [evaluation.feedback] : [],
    missingIdeas: !isCorrect ? ['Review the material and try again.'] : [],
    confidence: evaluation.confidence === 'high' ? 'High' : evaluation.confidence === 'low' ? 'Low' : 'Medium',
    nextActivity: isCorrect
      ? 'Move on to the next concept.'
      : 'Re-read the relevant section and retry.',
  }
}

export const apiStudySessionService: StudySessionService = {
  async getSession(sessionId: string): Promise<StudySessionDetail | undefined> {
    try {
      // Pattern: "COURSEID-next" means create a new session for that course
      if (sessionId.includes('-next')) {
        const rawCourseId = sessionId.replace(/-next$/, '')
        const courseId = parseInt(rawCourseId, 10)
        if (isNaN(courseId)) return undefined

        const response = await apiClient.post<BackendSession>('/sessions', {
          course_id: courseId,
          goal: 'Deep study session',
          knowledge_mode: 'course-grounded',
        })
        const backendSession = response.data
        sessionIdMap.set(sessionId, backendSession.id)

        const firstActivity = backendSession.activities[0]
        if (!firstActivity) return undefined

        const goal = backendSession.goal || 'Study session'
        return {
          id: sessionId,
          course: `Course #${backendSession.course_id}`,
          courseId: String(backendSession.course_id),
          topic: goal,
          goal,
          mode: backendSession.knowledge_mode === 'general' ? 'General knowledge' : 'Course-grounded',
          activityNumber: 1,
          activityTotal: 1,
          prompt: firstActivity.prompt,
          context: undefined,
          hints: [],
          explanation: '',
          sources: [],
          questions: [mapActivityToQuestion(firstActivity, goal)],
        }
      }

      // Numeric session id: load from backend
      const numericId = parseInt(sessionId, 10)
      if (!isNaN(numericId)) {
        const response = await apiClient.get<BackendSession>(`/sessions/${numericId}`)
        const backendSession = response.data
        sessionIdMap.set(sessionId, backendSession.id)

        const goal = backendSession.goal || 'Study session'
        const questions = backendSession.activities.map((a) =>
          mapActivityToQuestion(a, goal)
        )
        return {
          id: sessionId,
          course: `Course #${backendSession.course_id}`,
          courseId: String(backendSession.course_id),
          topic: goal,
          goal,
          mode: backendSession.knowledge_mode === 'general' ? 'General knowledge' : 'Course-grounded',
          activityNumber: 1,
          activityTotal: questions.length,
          prompt: questions[0]?.prompt ?? '',
          context: undefined,
          hints: [],
          explanation: '',
          sources: [],
          questions,
        }
      }

      return undefined
    } catch (err) {
      console.error('Failed to load session:', err)
      return undefined
    }
  },

  async evaluateAnswer(
    _sessionId: string,
    questionId: string,
    answer: string,
    _attempt: number
  ): Promise<StudyFeedback> {
    try {
      const activityId = parseInt(questionId, 10)
      if (isNaN(activityId)) throw new Error('Invalid activity id')

      const response = await apiClient.post<BackendEvaluation>(
        `/activities/${activityId}/attempts`,
        { answer, hint_count: 0 }
      )
      return mapEvaluationToFeedback(response.data)
    } catch (err) {
      console.error('Evaluation failed:', err)
      return {
        verdict: 'Insufficient evidence',
        strengths: [],
        missingIdeas: ['Could not evaluate — please check your connection and try again.'],
        confidence: 'Low',
        nextActivity: 'Retry the submission.',
      }
    }
  },

  async getNextQuestion(sessionId: string, answer: string): Promise<StudyQuestion | null> {
    try {
      const backendId = sessionIdMap.get(sessionId)
      if (!backendId) return null

      const response = await apiClient.post<BackendActivity>(`/sessions/${backendId}/next`, {
        answer,
        hint_count: 0,
      })
      const activity = response.data
      return mapActivityToQuestion(activity, 'Follow-up')
    } catch (err) {
      console.error('Failed to fetch next question:', err)
      return null
    }
  },
}
