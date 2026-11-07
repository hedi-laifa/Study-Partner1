import type {
  ExamAttempt,
  ExamCourseOption,
  ExamResult,
  ExamService,
  ExamSetup,
  PracticeExam,
} from '../contracts/exams'

const options: ExamCourseOption[] = [
  {
    id: 'deep-learning',
    title: 'Deep Learning',
    concepts: [
      { id: 'dl-1', title: 'Attention mechanisms' },
      { id: 'dl-2', title: 'Backpropagation' },
      { id: 'dl-3', title: 'Residual networks' },
      { id: 'dl-4', title: 'Batch normalization' },
    ],
  },
  {
    id: 'statistics',
    title: 'Statistics',
    concepts: [
      { id: 'stat-1', title: 'Hypothesis testing' },
      { id: 'stat-2', title: 'Confidence intervals' },
      { id: 'stat-3', title: 'Bayes theorem' },
      { id: 'stat-4', title: 'Maximum likelihood' },
    ],
  },
]

const attempts: ExamAttempt[] = [
  {
    id: 'attempt-1',
    title: 'Deep Learning Foundations',
    course: 'Deep Learning',
    date: '10 Nov',
    duration: '22 min',
    questionCount: 8,
    result: 'Passed',
    score: 87,
    completed: true,
  },
]

export const mockExamService: ExamService = {
  async getOptions(): Promise<ExamCourseOption[]> {
    return options
  },
  async listAttempts(): Promise<ExamAttempt[]> {
    return attempts
  },
  async createExam(setup: ExamSetup): Promise<PracticeExam> {
    return {
      ...setup,
      id: 'mock-exam-1',
      title: 'Practice Check-in',
      course: 'Deep Learning',
      topicTitles: setup.topicIds,
      questions: [
        {
          id: 'q1',
          prompt: 'What is the primary role of residual connections?',
          type: 'multiple-choice',
          options: [
            'Mitigate the vanishing gradient problem in deep networks',
            'Increase parameter count proportionally with depth',
            'Ensure zero activation values across layers',
          ],
          concept: 'Residual networks',
        },
      ],
    }
  },
  async getExam(id: string): Promise<PracticeExam | undefined> {
    return {
      id,
      courseId: '1',
      title: 'Practice Exam',
      course: 'Deep Learning',
      topicIds: [],
      topicTitles: ['Foundations'],
      questionCount: 5,
      timeLimit: 25,
      questions: [
        {
          id: 'q1',
          prompt: 'What is the primary role of residual connections?',
          type: 'multiple-choice',
          options: [
            'Mitigate the vanishing gradient problem in deep networks',
            'Increase parameter count proportionally with depth',
            'Ensure zero activation values across layers',
          ],
          concept: 'Residual networks',
        },
      ],
    }
  },
  async getResult(id: string): Promise<ExamResult | undefined> {
    return {
      examId: id,
      title: 'Practice Exam Result',
      course: 'Deep Learning',
      courseId: '1',
      completedQuestions: 1,
      totalQuestions: 1,
      timeUsed: '15 min',
      scoreLabel: '100%',
      counts: {
        Correct: 1,
        'Partially correct': 0,
        Incorrect: 0,
        'Insufficient evidence': 0,
      },
      questionResults: [
        {
          question: {
            id: 'q1',
            prompt: 'What is the primary role of residual connections?',
            type: 'multiple-choice',
            concept: 'Residual networks',
          },
          answer: 'Mitigate the vanishing gradient problem in deep networks',
          correctAnswer: 'Mitigate the vanishing gradient problem in deep networks',
          verdict: 'Correct',
          expectedIdeas: ['Mitigate vanishing gradients by providing skip connections'],
          strengths: ['Identified primary abstraction'],
          gaps: [],
          confidence: 'High',
        },
      ],
      concepts: [
        {
          concept: 'Residual networks',
          correct: 1,
          total: 1,
          summary: '1 of 1 questions answered correctly.',
          nextAction: 'Move to advanced architectures.',
        },
      ],
    }
  },
  async submitExam(id: string): Promise<ExamResult | undefined> {
    return this.getResult(id)
  },
}
